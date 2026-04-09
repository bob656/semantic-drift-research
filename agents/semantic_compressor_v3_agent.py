"""
semantic_compressor_v3_agent.py — 계약 히스토리 + Verifier 에이전트

## V2와의 차이

V2 (덮어쓰기):
  매 단계마다 AST 재추출 → 이전 계약 덮어씀
  → 부재 계약(absence contract)이 코드에 표현되지 않으므로 소실

V3 (히스토리 + Verifier):
  계약을 3가지 저장소로 분리 관리
    pinned  : 절대 제거 불가 (부재 계약, 불변식) — 항상 LLM 프롬프트에 포함
    active  : 현재 유효한 계약 — 프롬프트에 포함
    archived: 축약된 이전 계약 — 참조용, 프롬프트에 요약만 포함

  매 수정 단계마다 Verifier(LLM)가 새 코드를 검토하여
  기존 계약의 상태를 KEEP / UPDATE / ARCHIVE 중 하나로 판정
  → 컨텍스트 오염 없이 중요 계약을 영구 보존

## 이론적 근거

  Gotel & Finkelstein (1994): requirements rationale을 추적하지 않으면 이후 변경에서 위반
  Laban et al. (2505.06120): 초반 설계 결정이 후반에 앵커링 없이 덮임
  이 에이전트는 rationale을 pinned 계약으로 명시하여 앵커링을 강제함

## 논문 실험 위치

  Baseline (계약 없음)  →  드리프트 발생
  SemanticV2 (덮어쓰기) →  부재 계약 소실
  SemanticV3 (히스토리) →  부재 계약 보존 (이 에이전트)
"""
import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


# ── 계약 판정 결과 ──────────────────────────────────────────────
VERDICT_KEEP    = "KEEP"    # 여전히 유효, 변경 없음
VERDICT_UPDATE  = "UPDATE"  # 내용이 바뀜, 새 버전으로 교체
VERDICT_ARCHIVE = "ARCHIVE" # 더 이상 직접 관련 없음, 축약 보관


@dataclass
class Contract:
    """단일 계약 항목"""
    contract_id: str          # 고유 ID (예: "C001")
    content: str              # 계약 내용
    contract_type: str        # "absence" | "state" | "type" | "numeric"
    origin_step: int          # 최초 생성 단계
    pinned: bool = False      # True면 Verifier가 ARCHIVE 판정 불가
    version: int = 1          # 업데이트 횟수
    archived_summary: str = ""  # ARCHIVE 시 축약 내용


class SemanticCompressorV3Agent(BaseAgent):
    """
    계약 히스토리 + Verifier 기반 설계 의도 보존 에이전트.

    핵심 루프 (매 수정 단계):
      1. modify_code(): LLM이 계약을 참조하여 코드 수정
      2. _run_verifier(): Verifier LLM이 새 코드를 검토, 계약 판정
      3. _apply_verdicts(): 판정 결과로 계약 저장소 업데이트
    """

    # Verifier 프롬프트에서 판정을 파싱하는 패턴
    _VERDICT_PATTERN = re.compile(
        r'\[([A-Z0-9]+)\]\s*(KEEP|UPDATE|ARCHIVE)'
        r'(?:\s*\|\s*(.+?))?$',
        re.MULTILINE
    )

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        self._contracts: Dict[str, Contract] = {}  # contract_id → Contract
        self._step = 0
        self._next_id = 1
        self.verifier_log: List[Dict] = []  # Verifier 판정 이력

    # ── 공개 인터페이스 ────────────────────────────────────────────

    def solve_initial(self, task: str) -> str:
        response = self.call_llm(
            f"다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:\n\n{task}",
            "당신은 Python 개발자입니다. 타입 힌트를 사용하여 구현하세요."
        )
        code = self.extract_code(response)
        self._step = 0
        self._contracts = {}
        self._next_id = 1

        # step0에서 계약 초기화: AST + 프롬프트 의도 추출
        self._init_contracts_from_task_and_code(task, code)
        return code

    def solve_initial_from_code(self, code: str) -> None:
        self._step = 0
        self._contracts = {}
        self._next_id = 1
        self._init_contracts_from_code(code)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        self._step += 1

        # 1. 계약 참조 프롬프트로 코드 수정
        prompt = self._build_modify_prompt(current_code, modification_request)
        system = (
            "당신은 Python 개발자입니다.\n"
            "[PINNED] 계약은 어떤 경우에도 위반하지 마세요.\n"
            "[ACTIVE] 계약도 최대한 보존하면서 수정 요청을 구현하세요.\n"
            "완전한 Python 코드만 반환하세요."
        )
        new_code = self.extract_code(self.call_llm(prompt, system))

        # 2. Verifier가 계약 상태 판정
        verdicts = self._run_verifier(new_code, modification_request)

        # 3. 판정 결과로 계약 저장소 업데이트
        self._apply_verdicts(verdicts, new_code)

        return new_code

    # ── 계약 초기화 ────────────────────────────────────────────────

    def _init_contracts_from_task_and_code(self, task: str, code: str) -> None:
        """
        step0에서 두 소스로 계약을 초기화:
          1. 태스크 텍스트 → 부재 계약/불변식 추출 (LLM)
          2. 생성된 코드  → 타입/상태 계약 추출 (AST)
        """
        # 태스크에서 부재 계약 추출 (LLM 사용)
        absence_contracts = self._extract_absence_from_task(task)
        for content in absence_contracts:
            self._add_contract(content, "absence", pinned=True)

        # 코드에서 구조적 계약 추출 (AST)
        self._init_contracts_from_code(code)

    def _init_contracts_from_code(self, code: str) -> None:
        """AST로 타입/상태 계약 추출 후 pinned=False로 등록"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return

        # 타입 계약
        for line in self._extract_type_lines(tree):
            self._add_contract(line, "type", pinned=False)

        # 상태 전이 계약
        for line in self._extract_state_lines(tree, code):
            self._add_contract(line, "state", pinned=False)

    def _extract_absence_from_task(self, task: str) -> List[str]:
        """
        태스크 텍스트에서 부재 계약(하지 말아야 할 것)을 LLM으로 추출.

        예: "절대 삭제 불가" → "[부재 계약] 거래 삭제 금지 (del/pop 금지)"
        """
        prompt = f"""다음 요구사항 텍스트에서 "하지 말아야 할 것"에 해당하는 제약을 추출하세요.

요구사항:
{task}

출력 형식 (한 줄에 하나씩):
[부재 계약] <제약 내용>

제약이 없으면 빈 줄을 출력하세요.
코드 블록 없이 텍스트만 출력하세요."""

        response = self.call_llm(prompt,
            "당신은 소프트웨어 요구사항 분석가입니다. 요구사항에서 금지/불변 조건만 추출하세요.")

        contracts = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("[부재 계약]"):
                contracts.append(line)
        return contracts

    # ── Verifier ──────────────────────────────────────────────────

    def _run_verifier(self, new_code: str,
                      modification_request: str) -> Dict[str, str]:
        """
        Verifier LLM이 새 코드를 검토하여 각 계약의 상태를 판정.

        판정 기준:
          KEEP    : 계약이 새 코드에서도 유효
          UPDATE  : 계약 내용이 변경됨 (새 내용 제시)
          ARCHIVE : 계약이 더 이상 직접 관련 없음 (pinned는 ARCHIVE 불가)

        Returns: {contract_id: verdict_str}
        """
        if not self._contracts:
            return {}

        # Verifier에게 현재 계약 목록 전달
        contract_list = self._format_contracts_for_verifier()
        compressed_code = self.compress_code_for_context(new_code, max_body_lines=4)

        prompt = f"""다음 계약 목록을 검토하고 새 코드에서 각 계약의 상태를 판정하세요.

[수정 요청]
{modification_request[:300]}

[현재 계약 목록]
{contract_list}

[새 코드 (요약)]
```python
{compressed_code[:1500]}
```

각 계약에 대해 아래 형식으로 판정하세요:
[계약ID] KEEP
[계약ID] UPDATE | <새로운 계약 내용>
[계약ID] ARCHIVE | <한 줄 요약>

규칙:
- (PINNED) 표시된 계약은 ARCHIVE 불가. KEEP 또는 UPDATE만 가능.
- UPDATE는 계약 내용이 실제로 변경된 경우만 사용하세요.
- ARCHIVE는 이 계약이 현재 코드와 더 이상 관련 없을 때만 사용하세요."""

        response = self.call_llm(prompt,
            "당신은 코드 계약 검증자입니다. 각 계약 ID에 대해 정확한 형식으로만 판정하세요.")

        verdicts = {}
        for match in self._VERDICT_PATTERN.finditer(response):
            cid, verdict, extra = match.group(1), match.group(2), match.group(3)
            verdicts[cid] = (verdict, extra.strip() if extra else "")

        # Verifier 로그 기록 (JSON 직렬화 가능한 형태로 변환)
        serializable_verdicts = {
            cid: {'verdict': v[0], 'detail': v[1]} for cid, v in verdicts.items()
        }
        self.verifier_log.append({
            'step': self._step,
            'num_contracts': len(self._contracts),
            'verdicts': serializable_verdicts,
            'pinned_forced': []  # 아래에서 채움
        })

        return verdicts

    def _apply_verdicts(self, verdicts: Dict, new_code: str) -> None:
        """판정 결과를 계약 저장소에 반영"""
        forced = []

        for cid, contract in list(self._contracts.items()):
            if cid not in verdicts:
                continue

            verdict, extra = verdicts[cid]

            # pinned 계약에 ARCHIVE 판정 → 강제 KEEP
            if contract.pinned and verdict == VERDICT_ARCHIVE:
                verdict = VERDICT_KEEP
                forced.append(cid)

            if verdict == VERDICT_KEEP:
                pass  # 변경 없음

            elif verdict == VERDICT_UPDATE and extra:
                contract.content = extra
                contract.version += 1

            elif verdict == VERDICT_ARCHIVE:
                summary = extra or contract.content[:80]
                contract.archived_summary = summary
                # archived 계약은 content를 요약으로 교체 (프롬프트 토큰 절약)
                contract.content = f"[archived] {summary}"
                contract.contract_type = "archived"

        if self.verifier_log:
            self.verifier_log[-1]['pinned_forced'] = forced
            # 판정 후 계약 저장소 상태 스냅샷
            self.verifier_log[-1]['contract_state_after'] = {
                cid: {
                    'content': c.content,
                    'type': c.contract_type,
                    'pinned': c.pinned,
                    'version': c.version,
                }
                for cid, c in self._contracts.items()
            }

        # 새 코드에서 신규 계약 추출 (AST) 및 등록
        self._register_new_contracts_from_code(new_code)

    def _register_new_contracts_from_code(self, code: str) -> None:
        """
        새 코드에서 이전에 없던 타입/상태 계약을 추출해 active에 추가.
        이미 있는 계약은 중복 추가하지 않음.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return

        existing = {c.content for c in self._contracts.values()}

        for line in self._extract_type_lines(tree):
            if line not in existing:
                self._add_contract(line, "type", pinned=False)
                existing.add(line)

        for line in self._extract_state_lines(tree, code):
            if line not in existing:
                self._add_contract(line, "state", pinned=False)
                existing.add(line)

    # ── 프롬프트 빌더 ─────────────────────────────────────────────

    def _build_modify_prompt(self, current_code: str,
                              modification_request: str) -> str:
        pinned_section  = self._format_by_type(pinned_only=True)
        active_section  = self._format_by_type(pinned_only=False)
        archived_count  = sum(1 for c in self._contracts.values()
                              if c.contract_type == "archived")
        compressed_code = self.compress_code_for_context(current_code, max_body_lines=5)

        parts = [f"## 수정 요청\n{modification_request}"]

        if pinned_section:
            parts.append(
                f"## [PINNED] 절대 위반 금지 계약\n"
                f"아래 계약은 어떤 경우에도 지켜야 합니다:\n{pinned_section}"
            )
        if active_section:
            parts.append(
                f"## [ACTIVE] 현재 유효한 계약\n{active_section}"
            )
        if archived_count:
            parts.append(
                f"## [ARCHIVED] 이전 계약 ({archived_count}건, 참고용)\n"
                + self._format_archived()
            )

        parts.append(f"## 현재 코드\n```python\n{compressed_code}\n```")
        parts.append("위 계약을 모두 지키면서 수정 요청을 구현하세요. 완전한 Python 코드를 반환하세요.")

        return "\n\n".join(parts)

    def _format_contracts_for_verifier(self) -> str:
        lines = []
        for cid, c in self._contracts.items():
            if c.contract_type == "archived":
                continue
            pin_mark = " (PINNED)" if c.pinned else ""
            lines.append(f"[{cid}]{pin_mark} {c.content}")
        return "\n".join(lines) if lines else "(계약 없음)"

    def _format_by_type(self, pinned_only: bool) -> str:
        lines = []
        for c in self._contracts.values():
            if c.contract_type == "archived":
                continue
            if pinned_only and not c.pinned:
                continue
            if not pinned_only and c.pinned:
                continue
            lines.append(f"- {c.content}")
        return "\n".join(lines)

    def _format_archived(self) -> str:
        lines = []
        for c in self._contracts.values():
            if c.contract_type == "archived":
                lines.append(f"- {c.archived_summary or c.content}")
        return "\n".join(lines)

    # ── AST 추출 헬퍼 ─────────────────────────────────────────────

    def _extract_type_lines(self, tree: ast.AST) -> List[str]:
        lines = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    lines.append(
                        f"[타입 계약] {node.name}.{item.target.id}: {ast.unparse(item.annotation)}"
                    )
        return lines

    def _extract_state_lines(self, tree: ast.AST, code: str) -> List[str]:
        lines = []
        _STATE_KW = {'status', 'state', 'cancelled', 'pending', 'confirmed', 'active'}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                # status 할당 패턴 탐지
                for subnode in ast.walk(item):
                    if isinstance(subnode, ast.Assign):
                        for target in subnode.targets:
                            if (isinstance(target, ast.Attribute) and
                                    target.attr in _STATE_KW):
                                val = ast.unparse(subnode.value)
                                lines.append(
                                    f"[상태 계약] {node.name}.{item.name}(): "
                                    f"{target.attr} = {val}"
                                )

            # 부재 계약 — 상태 변경 메서드가 del/pop 없는 경우
            _PRESERVE = {'transactions', 'orders', 'items', 'records', 'history', 'payments'}
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                has_status_change = any(
                    isinstance(n, ast.Assign) and
                    any(isinstance(t, ast.Attribute) and t.attr in _STATE_KW
                        for t in n.targets)
                    for n in ast.walk(item)
                )
                if not has_status_change:
                    continue
                has_delete = any(
                    (isinstance(n, ast.Delete)) or
                    (isinstance(n, ast.Call) and
                     isinstance(getattr(n.func, 'attr', None), str) and
                     n.func.attr in ('pop', 'remove', 'clear'))
                    for n in ast.walk(item)
                )
                if not has_delete:
                    lines.append(
                        f"[보존 계약] {node.name}.{item.name}(): "
                        f"데이터 삭제 없이 상태만 변경 (del/pop 금지)"
                    )
        return lines

    # ── 내부 유틸 ─────────────────────────────────────────────────

    def _add_contract(self, content: str, contract_type: str,
                      pinned: bool) -> str:
        cid = f"C{self._next_id:03d}"
        self._next_id += 1
        self._contracts[cid] = Contract(
            contract_id=cid,
            content=content,
            contract_type=contract_type,
            origin_step=self._step,
            pinned=pinned,
        )
        return cid

    def get_contract_summary(self) -> Dict:
        """실험 결과에 포함할 계약 상태 요약"""
        pinned  = [c for c in self._contracts.values() if c.pinned]
        active  = [c for c in self._contracts.values()
                   if not c.pinned and c.contract_type != "archived"]
        archived = [c for c in self._contracts.values()
                    if c.contract_type == "archived"]
        return {
            'pinned_count':   len(pinned),
            'active_count':   len(active),
            'archived_count': len(archived),
            'verifier_steps': len(self.verifier_log),
            'pinned_contracts': [c.content for c in pinned],
        }
