"""
layered_memory_agent.py — 계층적 차등 요약 에이전트

## 핵심 아이디어

컨텍스트는 무한정 늘릴 수 없다. 그렇다고 균일하게 압축하면 중요한 정보를 잃는다.
해결책: 코드의 부분마다 다른 방식으로 기억한다.

## 3계층 메모리 구조

  Layer 1 — 영구 인터페이스 (Permanent Interface Contract)
    step0 코드에서 AST로 추출. 이후 절대 변경되지 않음.
    포함: 클래스 구조, 메서드 시그니처, 핵심 타입 패턴
    목적: "이 프로젝트는 Item(name, price, quantity) 객체를 사용한다"는 사실을 영구 보존

  Layer 2 — Delta 변경 이력 (Semantic Change Log)
    매 수정마다 "무엇이 의미적으로 바뀌었나"만 기록. 전체 코드 아님.
    포함: 새 클래스/메서드, 동작 변경(cancel_order 삭제→상태전환), 시그니처 확장
    목적: 8단계 수정 이력을 ~400 토큰으로 압축 (전체 코드 저장 시 ~6400 토큰)

  Layer 3 — 현재 코드 (Current Code, 항상 전체)
    current_code를 자르거나 요약하지 않고 그대로 전달.
    목적: ground truth 유지

## 토큰 예산

  Layer 1: ~200 토큰 (고정)
  Layer 2: ~50 토큰/수정 × 8단계 = ~400 토큰
  Layer 3: ~800 토큰 (현재 코드)
  합계:    ~1400 토큰 vs 전체 이력 보관 ~6400 토큰 → 4.5× 압축

## 관련 연구

  MemGPT (arxiv:2310.08560): 계층적 메모리 (working / long-term / episodic)
  Recursive Summarization (arxiv:2308.15022): 누적 요약
  LLMLingua (arxiv:2310.06839): 알고리즘적 압축으로 hallucination 제거
  Lost in the Middle (arxiv:2307.03172): 중요 정보를 앞/끝에 배치

## 프롬프트 구조

  [Layer 1 — 영구 인터페이스, 맨 앞]   ← Lost in the Middle: LLM 집중 구간
  [Layer 2 — Delta 이력, 중간]
  [Layer 3 — 현재 코드, 중간]
  [수정 요청, 맨 끝]                   ← LLM 집중 구간
"""
import ast
import re
from typing import Any, List
from .base_agent import BaseAgent

# Layer 2 Delta에서 강조할 핵심 동작 변경 패턴
_CRITICAL_BEHAVIOR_KEYWORDS = [
    'cancel', 'delete', 'remove', 'status', 'state',
    'payment', 'confirm', 'refund', 'inventory', 'stock',
    'customer', 'history',
]


class LayeredMemoryAgent(BaseAgent):
    """계층적 차등 요약으로 컨텍스트를 효율적으로 관리하는 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        # Layer 1: 영구 인터페이스 (step0에서 추출, 불변)
        self.permanent_interface: str = ""

        # Layer 2: Delta 변경 이력 (매 수정마다 누적, ~50토큰/항목)
        self.delta_log: List[str] = []

        self._step = 0

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial_from_code(self, code: str) -> None:
        """진단용: LLM 호출 없이 기존 코드로 Layer 1(영구 인터페이스)을 초기화한다."""
        self.permanent_interface = self._build_permanent_interface(code)
        self.delta_log = []
        self._step = 0

    def solve_initial(self, task: str) -> str:
        """
        초기 코드 생성 후 Layer 1(영구 인터페이스)을 설정한다.
        이 시점의 코드 구조가 전체 실험의 기준점이 된다.
        """
        response = self.call_llm(
            f"다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:\n\n{task}",
            "당신은 Python 개발자입니다. 타입 힌트를 사용하여 구현하세요."
        )
        code = self.extract_code(response)

        # Layer 1 설정 (단 1회, 이후 불변)
        self.permanent_interface = self._build_permanent_interface(code)
        self._step = 0
        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        3계층 메모리를 조합하여 수정을 수행한다.

        프롬프트 순서 (Lost in the Middle 전략):
          [Layer 1 — 맨 앞]  [Layer 2]  [Layer 3]  [요청 — 맨 끝]
        """
        self._step += 1

        prompt = self._build_prompt(current_code, modification_request)
        system = (
            "당신은 Python 개발자입니다.\n"
            "프롬프트 맨 앞 '영구 인터페이스'의 클래스 구조와 타입을 절대 변경하지 마세요.\n"
            "'변경 이력'에 기록된 동작 변경 사항을 모두 유지하세요."
        )

        new_code = self.extract_code(self.call_llm(prompt, system))

        # Layer 2 업데이트: 이번 수정의 Delta를 기록
        delta = self._extract_delta(modification_request, current_code, new_code)
        if delta:
            self.delta_log.append(f"수정{self._step}: {delta}")

        return new_code

    # ─── Layer 1: 영구 인터페이스 구축 ─────────────────────────────────────────

    def _build_permanent_interface(self, code: str) -> str:
        """
        step0 코드에서 영구 인터페이스를 구축한다.

        포함 내용:
          1. AST 추출: 클래스 구조 + 메서드 시그니처 (LLMLingua 인사이트)
          2. 핵심 메서드 스니펫: 타입 사용 패턴 직접 노출 (Chain of Density)
        """
        ast_part = self._extract_ast_structure(code)
        snippet_part = self._extract_type_pattern_snippets(code)

        result = "### 클래스 구조 · 시그니처 (변경 금지)\n" + ast_part
        if snippet_part:
            result += "\n\n### 타입 사용 패턴 (이 방식을 유지)\n" + snippet_part
        return result

    def _extract_ast_structure(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "(파싱 실패)"

        classes, sigs = [], []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            fields = self._get_fields(node)
            classes.append(f"- {node.name}: {fields}")
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith('_') and item.name != '__init__':
                    continue
                sig = self._format_sig(node.name, item)
                if sig:
                    sigs.append(f"- {sig}")

        out = []
        if classes:
            out.append("클래스:\n" + "\n".join(classes))
        if sigs:
            out.append("메서드:\n" + "\n".join(sigs))
        return "\n\n".join(out)

    def _extract_type_pattern_snippets(self, code: str) -> str:
        """
        타입 사용 패턴을 보여주는 핵심 메서드 스니펫 추출.
        "item.price * item.quantity" 같은 실제 접근 패턴을 LLM에 직접 노출한다.
        """
        target_methods = {'calculate_total', 'compute_total', 'add_order', '__init__'}
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ""

        lines = code.splitlines()
        snippets = []
        seen = set()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name not in target_methods or node.name in seen:
                continue
            seen.add(node.name)

            # 메서드 본문 최대 10줄
            start, end = node.lineno - 1, min(node.end_lineno, node.lineno + 9)
            body = "\n".join(lines[start:end])
            if end < node.end_lineno:
                body += "\n    ..."
            snippets.append(f"```python\n{body}\n```")

        return "\n".join(snippets)

    def _get_fields(self, class_node: ast.ClassDef) -> str:
        # 1순위: 클래스 레벨 어노테이션 (dataclass)
        annotated = [
            f"{n.target.id}({ast.unparse(n.annotation)})"
            for n in class_node.body
            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
        ]
        if annotated:
            return ", ".join(annotated)
        # 2순위: __init__ 파라미터
        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == '__init__':
                params = []
                for a in item.args.args[1:]:
                    hint = ast.unparse(a.annotation) if a.annotation else ""
                    params.append(f"{a.arg}({hint})" if hint else a.arg)
                return ", ".join(params) if params else "(없음)"
        return "(없음)"

    def _format_sig(self, class_name: str, func: ast.FunctionDef) -> str:
        if func.name == '__init__':
            return ""
        params = [a.arg for a in func.args.args if a.arg != 'self']
        ret = f" -> {ast.unparse(func.returns)}" if func.returns else ""
        return f"{class_name}.{func.name}({', '.join(params)}){ret}"

    # ─── Layer 2: Delta 변경 이력 추출 ──────────────────────────────────────────

    def _extract_delta(self, request: str, old_code: str, new_code: str) -> str:
        """
        수정 전후 코드를 비교하여 의미적 변경점만 추출한다.

        전체 코드를 저장하는 대신 "무엇이 바뀌었나"만 기록:
          추가된 클래스/메서드, 동작 변경, 시그니처 확장

        이 Delta 한 줄이 수백 줄 코드보다 중요한 의미적 정보를 담는다.
        """
        try:
            old_tree = ast.parse(old_code)
            new_tree = ast.parse(new_code)
        except SyntaxError:
            return self._summarize_request(request)

        old_methods = self._get_all_methods(old_tree)
        new_methods = self._get_all_methods(new_tree)
        old_classes = {n.name for n in ast.walk(old_tree) if isinstance(n, ast.ClassDef)}
        new_classes = {n.name for n in ast.walk(new_tree) if isinstance(n, ast.ClassDef)}

        added_classes  = new_classes - old_classes
        added_methods  = set(new_methods.keys()) - set(old_methods.keys())
        changed_sigs   = {
            name for name in (new_methods.keys() & old_methods.keys())
            if new_methods[name] != old_methods[name]
        }

        parts = []
        if added_classes:
            parts.append(f"새 클래스: {', '.join(sorted(added_classes))}")
        if added_methods:
            parts.append(f"새 메서드: {', '.join(sorted(added_methods))}")
        if changed_sigs:
            # 동작 변경이 중요한 메서드는 명시
            critical = [m for m in changed_sigs
                        if any(k in m.lower() for k in _CRITICAL_BEHAVIOR_KEYWORDS)]
            if critical:
                parts.append(f"동작 변경: {', '.join(sorted(critical))}")
            else:
                parts.append(f"시그니처 변경: {', '.join(sorted(changed_sigs))}")

        if not parts:
            return self._summarize_request(request)
        return " | ".join(parts)

    def _get_all_methods(self, tree) -> dict:
        """모든 클래스의 메서드와 시그니처를 수집한다."""
        result = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = [a.arg for a in item.args.args]
                    key = f"{node.name}.{item.name}"
                    result[key] = tuple(params)
        return result

    def _summarize_request(self, request: str) -> str:
        """AST 비교 실패 시 요청에서 핵심 키워드만 추출한다."""
        words = re.findall(r'[가-힣a-zA-Z_]{2,}', request)
        return " ".join(words[:8]) if words else request[:60]

    # ─── 프롬프트 구성 ──────────────────────────────────────────────────────────

    def _build_prompt(self, current_code: str, modification_request: str) -> str:
        """
        3계층 메모리를 조합하여 프롬프트를 구성한다.

        Lost in the Middle (Liu et al., 2024) 전략:
          - Layer 1(영구 인터페이스)을 맨 앞에 배치 → LLM이 가장 집중하는 위치
          - 수정 요청을 맨 끝에 배치 → LLM이 두 번째로 집중하는 위치
          - 긴 현재 코드는 중간에 배치 (필요하지만 lost해도 Layer 1이 보완)
        """
        # Layer 2: Delta 이력 (있을 경우만 포함, 토큰 절약)
        delta_section = ""
        if self.delta_log:
            # 오래된 항목은 앞에서 압축 (최근 6개만 유지)
            recent = self.delta_log[-6:]
            if len(self.delta_log) > 6:
                old_summary = f"[이전 {len(self.delta_log)-6}개 수정: 생략]"
                history = "\n".join([old_summary] + [f"- {d}" for d in recent])
            else:
                history = "\n".join(f"- {d}" for d in recent)
            delta_section = f"\n\n## 변경 이력 (Delta Log)\n{history}"

        return f"""## 영구 인터페이스 (step0 기준 — 절대 변경 금지)
{self.permanent_interface}{delta_section}

---

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**영구 인터페이스의 클래스 구조·타입을 유지하고, 변경 이력의 모든 동작 변경을 보존하면서**
수정 요청만 구현하세요. 완전한 수정된 코드를 작성하세요."""
