"""
guideline_agent.py — 초기 성공 코드 기반 불변 가이드라인 에이전트

## 핵심 아이디어

기존 접근법의 공통 실패 원인:
  StateDoc   → 코드 생성 전에 추상 문서 작성 → 타입 재해석 발생
  CoTDoc-LLM → 매 단계 LLM이 요약 → hallucination 누적
  CoTDoc-AST → 매 단계 현재 코드 분석 → 오류 있는 코드가 기준이 됨

GuidelineAgent의 전략:
  step0(초기 코드)는 실험 전체에서 거의 항상 10점 → ground truth
  이 코드에서 가이드라인을 단 한 번 추출하고, 이후 모든 수정에 불변으로 사용

  "처음 제대로 만든 코드의 패턴을 끝까지 강제한다"

## 가이드라인 구성 (2-layer)

  Layer 1 — AST 추출 (LLMLingua 인사이트: LLM 없이 100% 정확)
    · 클래스 구조와 필드 타입
    · 모든 public 메서드 시그니처

  Layer 2 — 핵심 메서드 스니펫 (Chain of Density 원칙: 실제 코드가 최고 밀도)
    · calculate_total, add_order, __init__ 등 타입 사용 패턴을 보여주는 메서드 본문
    · "item.price" vs "item[0]" 같은 실제 접근 패턴을 LLM에게 직접 보여줌

## 프롬프트 구조 (Lost in the Middle 역이용)

  [가이드라인 — 짧고 구체적, 맨 앞]  ← LLM 집중 구간 (step0 기준, 불변)
  [현재 코드]
  [수정 요청 — 맨 끝]                ← LLM 집중 구간

## 기존 접근법과의 차이

  StateDoc   : 추상 문서 (LLM 생성, 코드 전 작성)
  CoTDoc     : 현재 코드의 요약 (매 단계 갱신, 오류 누적 가능)
  Guideline  : step0 코드의 구체적 패턴 (1회 추출, 불변, 항상 정확)

## LLM 호출 횟수

  BaselineAgent  : 수정당 1회
  GuidelineAgent : 수정당 1회 (가이드라인 추출은 AST — LLM 호출 없음)
"""
import ast
from typing import Any
from .base_agent import BaseAgent

# 가이드라인에 포함할 핵심 메서드 이름 목록
# 이 메서드들의 본문이 타입 사용 패턴을 가장 잘 드러냄
_KEY_METHOD_NAMES = {
    'calculate_total', 'compute_total',
    'add_order', 'create_order',
    '__init__',
}


class GuidelineAgent(BaseAgent):
    """초기 성공 코드에서 가이드라인을 추출하고 전체 수정에 불변으로 유지하는 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        # step0에서 단 한 번 설정되고 이후 절대 변경되지 않는 가이드라인
        self.guideline: str = ""

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial(self, task: str) -> str:
        """
        초기 코드를 생성하고 그 코드에서 가이드라인을 추출한다.

        가이드라인은 이 시점에 단 한 번 설정되며 이후 절대 수정되지 않는다.
        step0 코드가 ground truth가 된다.
        """
        system_prompt = "당신은 Python 개발자입니다. 요구사항을 정확히 구현하세요."
        prompt = f"""다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:

{task}

- 데이터 클래스(dataclass) 또는 일반 클래스를 사용하세요
- 타입 힌트를 포함하면 좋습니다
- 완전한 실행 가능한 코드를 작성하세요"""

        response = self.call_llm(prompt, system_prompt)
        code = self.extract_code(response)

        # step0 코드에서 가이드라인 1회 추출 (이후 불변)
        self.guideline = self._build_guideline(code)
        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        가이드라인(step0 기준, 불변)을 맨 앞에 배치하고 수정을 수행한다.

        Lost in the Middle (Liu et al., 2024) 전략:
          [가이드라인 — 맨 앞, LLM 집중]
          [현재 코드]
          [수정 요청 — 맨 끝, LLM 집중]
        """
        system_prompt = (
            "당신은 Python 개발자입니다.\n"
            "프롬프트 맨 앞의 '구현 가이드라인'에 명시된 클래스 구조와 메서드 시그니처를 "
            "절대 변경하지 마세요. 새 기능만 추가하세요."
        )

        prompt = f"""## 구현 가이드라인 (초기 코드 기준 — 절대 변경 금지)
{self.guideline}

---

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**위 가이드라인의 클래스 구조·메서드 시그니처·타입 패턴을 그대로 유지하면서**
수정 요청만 구현하세요. 완전한 수정된 코드를 작성하세요."""

        response = self.call_llm(prompt, system_prompt)
        return self.extract_code(response)

    # ─── 가이드라인 구축 ────────────────────────────────────────────────────────

    def _build_guideline(self, code: str) -> str:
        """
        step0 코드에서 2-layer 가이드라인을 구축한다.

        Layer 1 (AST): 클래스 구조 + 메서드 시그니처 — 정확한 계약 정의
        Layer 2 (스니펫): 핵심 메서드 본문 — 실제 타입 사용 패턴 직접 노출
        """
        layer1 = self._extract_structure(code)
        layer2 = self._extract_key_snippets(code)

        parts = [layer1]
        if layer2:
            parts.append(
                "## 핵심 구현 패턴 (타입 사용 방식 — 이 패턴을 유지하세요)\n" + layer2
            )
        return "\n\n".join(parts)

    # ─── Layer 1: AST 구조 추출 ─────────────────────────────────────────────────

    def _extract_structure(self, code: str) -> str:
        """
        AST로 클래스 구조와 메서드 시그니처를 추출한다 (LLMLingua 인사이트).
        LLM 없이 파싱하므로 hallucination이 발생하지 않는다.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "(AST 파싱 실패)"

        classes, methods = [], []

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
                    methods.append(f"- {sig}")

        parts = []
        if classes:
            parts.append("## 클래스 구조 (변경 금지)\n" + "\n".join(classes))
        if methods:
            parts.append("## 메서드 시그니처 (변경 금지)\n" + "\n".join(methods))
        return "\n\n".join(parts) if parts else "(클래스 없음)"

    def _get_fields(self, class_node: ast.ClassDef) -> str:
        """클래스 필드를 추출한다. dataclass 어노테이션 또는 __init__ 파라미터 사용."""
        # 1순위: 클래스 레벨 어노테이션 (dataclass 스타일)
        annotated = []
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                annotated.append(f"{item.target.id}({ast.unparse(item.annotation)})")
        if annotated:
            return ", ".join(annotated)

        # 2순위: __init__ 파라미터
        for item in class_node.body:
            if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == '__init__'):
                params = []
                for a in item.args.args[1:]:  # self 제외
                    hint = ast.unparse(a.annotation) if a.annotation else ""
                    params.append(f"{a.arg}({hint})" if hint else a.arg)
                return ", ".join(params) if params else "(필드 없음)"

        return "(필드 없음)"

    def _format_sig(self, class_name: str, func_node) -> str:
        """메서드 시그니처를 포맷한다."""
        if func_node.name == '__init__':
            return ""
        params = [a.arg for a in func_node.args.args if a.arg != 'self']
        ret = f" -> {ast.unparse(func_node.returns)}" if func_node.returns else ""
        return f"{class_name}.{func_node.name}({', '.join(params)}){ret}"

    # ─── Layer 2: 핵심 메서드 스니펫 추출 ──────────────────────────────────────

    def _extract_key_snippets(self, code: str) -> str:
        """
        타입 사용 패턴을 드러내는 핵심 메서드의 실제 코드 스니펫을 추출한다.

        Chain of Density 원칙:
          추상적 설명("items는 List[Item]") 대신
          실제 코드("for item in items: total += item.price * item.quantity")를 직접 보여준다.
          LLM이 item.price 패턴을 보면 item[0]이나 튜플 언패킹으로 바꾸기 어렵다.

        추출 대상:
          - calculate_total, compute_total: item.price/item.quantity 접근 패턴
          - add_order, create_order: items 파라미터 타입 패턴
          - Order.__init__: items 필드 초기화 패턴
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ""

        lines = code.splitlines()
        snippets = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name not in _KEY_METHOD_NAMES:
                continue

            # 메서드 본문 추출 (최대 12줄)
            start = node.lineno - 1
            end = min(node.end_lineno, start + 12)
            snippet_lines = lines[start:end]
            if end < node.end_lineno:
                snippet_lines.append("    ...")

            # 소속 클래스 이름 찾기
            class_name = self._find_class_of_method(tree, node.name)
            header = f"# {class_name}.{node.name}" if class_name else f"# {node.name}"

            snippets.append(header + "\n" + "\n".join(snippet_lines))

        return "\n\n".join(snippets)

    def _find_class_of_method(self, tree, method_name: str) -> str:
        """메서드가 속한 클래스 이름을 찾는다."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name == method_name):
                    return node.name
        return ""
