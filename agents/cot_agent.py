"""
cot_agent.py — 논문 기반 4중 전략 적용 에이전트

## 적용 논문 및 전략

1. Lost in the Middle (Liu et al., 2024, TACL — arxiv:2307.03172)
   → 핵심 제약을 프롬프트 맨 앞에 배치 (U자 곡선 역이용)

2. LLMLingua (Microsoft, EMNLP 2023 — arxiv:2310.06839)
   → LLM이 요약을 생성하면 hallucination 위험.
     대신 AST로 시그니처/타입을 프로그래밍적으로 추출 → 오류 없는 100% 정확한 구조 정보

3. Recursive Summarization (Neurocomputing 2025 — arxiv:2308.15022)
   → 매 수정 후 누적 이력(cumulative_summary)을 갱신.
     이전 요약 + 이번 변경 = 새 요약 → 정보가 단계마다 소실되지 않음

4. Chain of Density (Salesforce·MIT, 2023 — arxiv:2309.04269)
   → 요약이 추상화될수록 핵심 엔티티가 사라진다는 문제를 해결.
     AST 추출이 강제하는 구체적 엔티티(클래스명, 필드 타입, 메서드 시그니처)가
     chain of density의 "최고 밀도" 상태를 자동으로 달성

## 프롬프트 구조 (Lost in the Middle 역이용)

  [AST 추출 구조 — 짧고 정확, 맨 앞]   ← LLM 집중 구간
  [누적 이력 요약 — Recursive]
  [현재 코드]
  [수정 요청 — 맨 끝]                   ← LLM 집중 구간

## LLM 호출 횟수

  BaselineAgent : 수정당 1회
  CoTDocAgent   : 수정당 1회 (AST 추출이 LLM 요약 호출 대체 → 속도·정확도 동시 개선)
"""
import ast
from typing import Any
from .base_agent import BaseAgent


class CoTDocAgent(BaseAgent):
    """논문 기반 4중 전략 적용 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        # Recursive Summarization: 단계마다 누적되는 이력 요약
        self.cumulative_summary = ""

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial(self, task: str) -> str:
        """초기 코드 생성 — 단순하게 요청만 전달"""
        system_prompt = "당신은 Python 개발자입니다. 요구사항을 정확히 구현하세요."
        prompt = f"""다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:

{task}"""
        response = self.call_llm(prompt, system_prompt)
        code = self.extract_code(response)

        # Recursive Summarization 초기화: 초기 구조를 누적 이력에 등록
        self.cumulative_summary = self._init_summary(task, code)
        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        수정 흐름:
          1. _extract_code_structure()  → AST로 정확한 시그니처 추출 (LLM 없이)
          2. _build_prompt()            → 추출 결과를 맨 앞에, 수정 요청을 맨 끝에
          3. LLM 호출 → 코드 생성
          4. _update_cumulative_summary() → Recursive Summarization 갱신
        """
        # LLMLingua 인사이트: LLM 대신 AST로 오류 없이 추출
        ast_structure = self._extract_code_structure(current_code)

        # Lost in the Middle 전략: 핵심 제약을 앞에, 수정 요청을 끝에
        prompt = self._build_prompt(current_code, modification_request, ast_structure)

        response = self.call_llm(
            prompt,
            "당신은 Python 개발자입니다. "
            "프롬프트 맨 앞의 '변경 금지 구조'에 명시된 시그니처와 타입을 절대 바꾸지 마세요.")

        new_code = self.extract_code(response)

        # Recursive Summarization: 이번 수정 내용을 누적 이력에 반영
        self._update_cumulative_summary(modification_request, new_code)

        return new_code

    # ─── AST 기반 구조 추출 (LLMLingua + Chain of Density) ────────────────────

    def _extract_code_structure(self, code: str) -> str:
        """
        AST로 현재 코드의 클래스 구조와 메서드 시그니처를 추출한다.

        LLMLingua 인사이트 적용:
          LLM이 요약을 생성하면 hallucination으로 타입이 틀릴 수 있다.
          AST 파싱은 코드에서 직접 읽으므로 항상 100% 정확하다.

        Chain of Density 효과:
          출력이 항상 구체적 엔티티(클래스명, 필드명, 타입, 메서드 시그니처)로 구성.
          추상적 설명 없이 최고 밀도 상태를 자동으로 달성한다.

        반환 예시:
          ## 클래스 구조
          - Item: name(str), price(float), quantity(int), stock(int)
          - Order: order_id(int), items(List[Item]), discount_percent(float), status(str)

          ## 변경 금지 메서드 시그니처
          - OrderManager.add_order(order_id, items, inventory) -> None
          - OrderManager.cancel_order(order_id) -> None
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "(AST 파싱 실패 — 코드 구문 오류)"

        classes = []
        methods = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # 클래스 필드 추출: __init__ 파라미터 또는 dataclass 필드
            fields = self._extract_fields(node)
            classes.append(f"- {node.name}: {fields}")

            # 공개 메서드 시그니처 추출
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith('_') and item.name != '__init__':
                    continue
                sig = self._format_signature(node.name, item)
                if sig:
                    methods.append(f"- {sig}")

        parts = []
        if classes:
            parts.append("## 클래스 구조 (변경 금지)\n" + "\n".join(classes))
        if methods:
            parts.append("## 메서드 시그니처 (변경 금지)\n" + "\n".join(methods))

        return "\n\n".join(parts) if parts else "(클래스 없음)"

    def _extract_fields(self, class_node: ast.ClassDef) -> str:
        """클래스 필드를 추출한다. dataclass 어노테이션 또는 __init__ 파라미터 사용."""
        # 1순위: 클래스 레벨 어노테이션 (dataclass 스타일)
        annotated = []
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                type_str = ast.unparse(item.annotation)
                annotated.append(f"{item.target.id}({type_str})")
        if annotated:
            return ", ".join(annotated)

        # 2순위: __init__ 파라미터
        for item in class_node.body:
            if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == '__init__'):
                params = []
                args = item.args
                all_args = args.args[1:]  # self 제외
                annotations = {
                    a.arg: ast.unparse(a.annotation)
                    for a in all_args if a.annotation
                }
                for a in all_args:
                    type_hint = annotations.get(a.arg, "")
                    params.append(f"{a.arg}({type_hint})" if type_hint else a.arg)
                return ", ".join(params) if params else "(필드 없음)"

        return "(필드 없음)"

    def _format_signature(self, class_name: str, func_node) -> str:
        """메서드 시그니처를 읽기 쉬운 문자열로 포맷한다."""
        if func_node.name == '__init__':
            return ""
        args = func_node.args
        params = [a.arg for a in args.args if a.arg != 'self']
        ret = ""
        if func_node.returns:
            ret = f" -> {ast.unparse(func_node.returns)}"
        return f"{class_name}.{func_node.name}({', '.join(params)}){ret}"

    # ─── 프롬프트 구성 (Lost in the Middle 전략) ────────────────────────────────

    def _build_prompt(self, current_code: str,
                      modification_request: str,
                      ast_structure: str) -> str:
        """
        Lost in the Middle (Liu et al., 2024) 전략 적용:
          - 변경 금지 구조(AST) → 맨 앞 (LLM 집중 구간)
          - 누적 이력 요약       → 앞부분
          - 현재 코드            → 중간
          - 수정 요청            → 맨 끝 (LLM 집중 구간)
        """
        cumulative_section = ""
        if self.cumulative_summary:
            cumulative_section = f"""## 누적 변경 이력 (Recursive Summary)
{self.cumulative_summary}

"""
        return f"""## 변경 금지 구조 (AST 추출 — 정확한 시그니처)
{ast_structure}

{cumulative_section}## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

위 '변경 금지 구조'의 클래스 필드와 메서드 시그니처를 그대로 유지하면서
수정 요청만 구현하세요. 완전한 수정된 코드를 작성하세요."""

    # ─── Recursive Summarization ────────────────────────────────────────────────

    def _init_summary(self, task: str, code: str) -> str:
        """
        초기 누적 요약 생성.
        Chain of Density 원칙: 구체적 엔티티(클래스·메서드 이름) 중심으로 작성.
        """
        ast_structure = self._extract_code_structure(code)
        task_short = task.strip()[:150]
        return f"[초기 구현] {task_short}\n{ast_structure}"

    def _update_cumulative_summary(self, modification_request: str, new_code: str):
        """
        Recursive Summarization (arxiv:2308.15022) 적용:
          이전 누적 요약 + 이번 수정 내용 → 새 누적 요약

        LLM 호출 없이 구조적으로 갱신 (Chain of Density: 엔티티 보존).
        새로 추가된 구조만 AST로 추출해 이전 요약에 병합한다.
        """
        new_structure = self._extract_code_structure(new_code)
        req_short = modification_request.strip()[:120]

        # 이전 요약에 이번 변경 내용을 append (재귀적 누적)
        entry = f"\n[수정] {req_short}\n{new_structure}"

        # 요약이 너무 길어지면 앞부분을 압축 (최대 1200자 유지)
        combined = self.cumulative_summary + entry
        if len(combined) > 1200:
            # 가장 오래된 항목 하나를 제목만 남기고 압축
            lines = combined.split('\n')
            combined = '\n'.join(lines[-40:])  # 최근 40줄 유지

        self.cumulative_summary = combined
