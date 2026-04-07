"""
semantic_compressor_agent.py — 의미론적 중요도 기반 압축 에이전트

## LayeredMemoryAgent와의 차이

LayeredMemory는 코드를 *구조적*으로 분할한다:
  Layer 1 = AST 구조, Layer 2 = Delta 이력, Layer 3 = 현재 코드

SemanticCompressor는 코드를 *의미론적 중요도* 기준으로 압축한다:
  같은 토큰 예산이라면, "이 정보가 미래 수정에서 깨질 위험이 높은가"를
  기준으로 보존 여부를 결정한다.

## 3가지 핵심 분석 (모두 AST + 정적 분석, LLM 미사용)

  1. 타입 계약 (Type Contracts)
     - 필드 타입: Item.price: float → calculate_total()이 직접 의존
     - 파라미터 타입: add_order(items: List[Item]) → 호출부 영향
     - 반환 타입: get_order() -> Optional[Order]

  2. 상태 전이 규칙 (State Transition Rules)
     - Enum 값 탐지: OrderStatus.CANCELLED, SHIPPED, REFUNDED
     - .status 할당 패턴: order.status = ... 위치 추적
     - 상태 의존 분기: if order.status == ... 패턴

  3. 메서드 간 의존성 (Cross-Method Dependencies)
     - 속성 접근 추적: calculate_total()에서 item.price 접근
     - 메서드 호출 그래프: confirm_order() → process_payment() 호출 여부
     - 이 의존성이 깨지면 AttributeError/TypeError 발생 → 드리프트의 직접 원인

## 중요도 가중 압축 (Importance-Weighted Compression)

Delta 이력을 균일하게 기록하는 대신, 변경의 *의미론적 위험도*에 따라 토큰 배정:

  HIGH (50토큰): 타입 계약 변경, 상태머신 도입/변경
  MEDIUM (30토큰): 새 클래스/메서드 추가, 시그니처 확장
  LOW (10토큰): 기능 추가 (기존 계약 유지)

## 관련 연구

  LLMLingua (arxiv:2310.06839): 중요도 점수 기반 토큰 압축
  RECOMP (arxiv:2310.11343): 태스크 관련 정보만 선택적 압축
  Chain of Density (arxiv:2309.04269): 반복 압축으로 밀도 향상
  Information Bottleneck (Tishby et al.): 미래 예측에 필요한 정보만 보존
"""
import ast
import re
from typing import Any, Dict, List, Set, Tuple
from .base_agent import BaseAgent


# 상태 관련 키워드 — 상태 전이 규칙 탐지에 사용
_STATE_KEYWORDS = {'status', 'state', 'cancelled', 'shipped', 'refunded',
                   'pending', 'confirmed', 'paid', 'active', 'inactive'}

# 계약 위반 시 즉시 드리프트를 유발하는 고위험 변경 패턴
_HIGH_RISK_KEYWORDS = {'cancel', 'status', 'state', 'price', 'type',
                       'payment', 'refund', 'inventory', 'stock'}

# Delta 중요도 등급
_IMPORTANCE_HIGH   = "HIGH"
_IMPORTANCE_MEDIUM = "MEDIUM"
_IMPORTANCE_LOW    = "LOW"


class SemanticCompressorAgent(BaseAgent):
    """의미론적 중요도 기반 압축으로 behavioral contract를 보존하는 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        # Layer 1: 의미론적 계약 (step0에서 정적 분석, 불변)
        self.semantic_contracts: str = ""

        # Layer 2: 중요도 가중 Delta 이력
        # 각 항목: {'step': int, 'importance': str, 'delta': str}
        self.weighted_deltas: List[Dict] = []

        self._step = 0

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial_from_code(self, code: str) -> None:
        """진단용: LLM 호출 없이 기존 코드로 의미론적 계약을 초기화한다."""
        self.semantic_contracts = self._extract_semantic_contracts(code)
        self.weighted_deltas = []
        self._step = 0

    def solve_initial(self, task: str) -> str:
        response = self.call_llm(
            f"다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:\n\n{task}",
            "당신은 Python 개발자입니다. 타입 힌트를 사용하여 구현하세요."
        )
        code = self.extract_code(response)
        self.semantic_contracts = self._extract_semantic_contracts(code)
        self._step = 0
        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        self._step += 1

        prompt = self._build_prompt(current_code, modification_request)
        system = (
            "당신은 Python 개발자입니다.\n"
            "'의미론적 계약' 섹션의 타입·상태·의존성을 절대 깨지 마세요.\n"
            "계약을 유지하면서 수정 요청만 구현하세요."
        )

        new_code = self.extract_code(self.call_llm(prompt, system))

        delta = self._extract_weighted_delta(modification_request, current_code, new_code)
        if delta:
            self.weighted_deltas.append(delta)

        return new_code

    # ─── Layer 1: 의미론적 계약 추출 ────────────────────────────────────────────

    def _extract_semantic_contracts(self, code: str) -> str:
        """
        step0 코드에서 3종류의 의미론적 계약을 정적 분석으로 추출한다.
        LLM을 사용하지 않아 hallucination이 없다.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "(파싱 실패)"

        type_contracts   = self._extract_type_contracts(tree, code)
        state_rules      = self._extract_state_transition_rules(tree, code)
        dependencies     = self._extract_cross_method_dependencies(tree, code)

        sections = []
        if type_contracts:
            sections.append("### 타입 계약 (Type Contracts)\n" + type_contracts)
        if state_rules:
            sections.append("### 상태 전이 규칙 (State Rules)\n" + state_rules)
        if dependencies:
            sections.append("### 메서드 간 의존성 (Dependencies)\n" + dependencies)

        return "\n\n".join(sections) if sections else "(계약 없음)"

    def _extract_type_contracts(self, tree: ast.AST, code: str) -> str:
        """
        필드 타입, 파라미터 타입, 반환 타입을 추출한다.

        예: Item.price: float, add_order(items: List[Item]) -> Order
        이 정보가 없으면 LLM이 item.price를 튜플 접근으로 재해석할 수 있다.
        """
        lines = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # 1. dataclass 필드 타입 (AnnAssign)
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    type_str = ast.unparse(item.annotation)
                    lines.append(f"- {node.name}.{item.target.id}: {type_str}")

            # 2. __init__ 파라미터 타입
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name == '__init__':
                    for arg in item.args.args[1:]:  # self 제외
                        if arg.annotation:
                            lines.append(
                                f"- {node.name}.__init__.{arg.arg}: {ast.unparse(arg.annotation)}"
                            )

            # 3. 공개 메서드 시그니처 (파라미터 타입 + 반환 타입)
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith('_'):
                    continue
                params = []
                for arg in item.args.args[1:]:  # self 제외
                    if arg.annotation:
                        params.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
                    else:
                        params.append(arg.arg)
                ret = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                if params or ret:
                    lines.append(
                        f"- {node.name}.{item.name}({', '.join(params)}){ret}"
                    )

        return "\n".join(lines)

    def _extract_state_transition_rules(self, tree: ast.AST, code: str) -> str:
        """
        상태 머신 규칙을 추출한다.

        탐지 대상:
          1. Enum 클래스 + 그 값들
          2. .status = ... 할당 (어느 메서드에서 발생하는가)
          3. if ... status == ... 조건 분기
        """
        lines = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # 1. Enum 클래스 탐지
            is_enum = any(
                (isinstance(b, ast.Name) and b.id == 'Enum') or
                (isinstance(b, ast.Attribute) and b.attr == 'Enum')
                for b in node.bases
            )
            if is_enum:
                values = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for t in item.targets:
                            if isinstance(t, ast.Name):
                                values.append(t.id)
                if values:
                    lines.append(f"- Enum {node.name}: {', '.join(values)}")

            # 2. 메서드별 .status 할당 추적
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                status_assignments = []
                for n in ast.walk(item):
                    if (isinstance(n, ast.Assign) and
                            any(
                                isinstance(t, ast.Attribute) and t.attr in _STATE_KEYWORDS
                                for t in n.targets
                            )):
                        try:
                            val = ast.unparse(n.value)
                            status_assignments.append(val)
                        except Exception:
                            pass
                if status_assignments:
                    lines.append(
                        f"- {node.name}.{item.name}() 상태 변경: {', '.join(status_assignments)}"
                    )

            # 3. 상태 의존 조건 분기 (raise/if)
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for n in ast.walk(item):
                    if isinstance(n, ast.Raise) and n.exc:
                        exc_str = ast.unparse(n.exc)
                        if any(k in exc_str.lower() for k in _STATE_KEYWORDS):
                            lines.append(
                                f"- {node.name}.{item.name}() raises: {exc_str[:60]}"
                            )

        return "\n".join(lines)

    def _extract_cross_method_dependencies(self, tree: ast.AST, code: str) -> str:
        """
        메서드 간 속성 접근 의존성을 추출한다.

        핵심: calculate_total()이 item.price에 접근한다는 사실을 보존하면
        나중에 Item 클래스가 바뀌어도 calculate_total() 호출부가 깨지지 않는다.

        탐지:
          - 메서드 내 obj.attr 접근 패턴 → obj 타입 추론 후 의존성 기록
          - 메서드가 다른 메서드를 직접 호출하는 패턴
        """
        lines = []

        # 클래스별 필드 이름 수집 (타입 추론에 사용)
        class_fields: Dict[str, Set[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                fields = set()
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        fields.add(item.target.id)
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == '__init__':
                        for arg in item.args.args[1:]:
                            fields.add(arg.arg)
                class_fields[node.name] = fields

        # 메서드 내 attr 접근 패턴 분석
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith('_') and item.name != '__init__':
                    continue

                # 이 메서드에서 접근하는 외부 객체 속성들
                accesses: List[str] = []
                for n in ast.walk(item):
                    if isinstance(n, ast.Attribute):
                        # self.x 는 제외, 그 외 obj.attr 패턴 수집
                        if isinstance(n.value, ast.Name) and n.value.id != 'self':
                            obj_name = n.value.id
                            attr_name = n.attr
                            # 알려진 클래스 필드인 경우만 기록
                            for cls_name, fields in class_fields.items():
                                if attr_name in fields and cls_name != node.name:
                                    accesses.append(f"{cls_name}.{attr_name}")

                if accesses:
                    unique = sorted(set(accesses))
                    lines.append(
                        f"- {node.name}.{item.name}() 접근: {', '.join(unique)}"
                    )

        return "\n".join(lines)

    # ─── Layer 2: 중요도 가중 Delta ──────────────────────────────────────────────

    def _extract_weighted_delta(
        self, request: str, old_code: str, new_code: str
    ) -> Dict:
        """
        변경의 의미론적 위험도를 평가하고 중요도를 부여한다.

        HIGH:   타입 계약 변경, 상태머신 도입/변경 → 계약 위반 위험
        MEDIUM: 새 클래스/메서드, 시그니처 확장 → 호환성 영향
        LOW:    기능 추가 (기존 계약 유지) → 단순 확장
        """
        try:
            old_tree = ast.parse(old_code)
            new_tree = ast.parse(new_code)
        except SyntaxError:
            return {
                'step': self._step,
                'importance': _IMPORTANCE_MEDIUM,
                'delta': self._summarize_request(request)
            }

        old_methods  = self._get_method_sigs(old_tree)
        new_methods  = self._get_method_sigs(new_tree)
        old_classes  = self._get_class_names(old_tree)
        new_classes  = self._get_class_names(new_tree)
        old_types    = self._get_type_annotations(old_tree)
        new_types    = self._get_type_annotations(new_tree)
        old_enums    = self._get_enum_classes(old_tree)
        new_enums    = self._get_enum_classes(new_tree)

        added_classes   = new_classes - old_classes
        added_methods   = set(new_methods) - set(old_methods)
        changed_sigs    = {
            k for k in (new_methods.keys() & old_methods.keys())
            if new_methods[k] != old_methods[k]
        }
        changed_types   = {
            k for k in (new_types.keys() & old_types.keys())
            if new_types[k] != old_types[k]
        }
        added_enums     = new_enums - old_enums

        # 중요도 판정
        importance = _IMPORTANCE_LOW
        parts = []

        # HIGH: 타입 계약 변경 or 상태머신 변경
        if changed_types:
            importance = _IMPORTANCE_HIGH
            parts.append(f"타입변경: {', '.join(sorted(changed_types))}")
        if added_enums:
            importance = _IMPORTANCE_HIGH
            parts.append(f"상태머신 추가: {', '.join(sorted(added_enums))}")
        high_risk_sigs = [
            m for m in changed_sigs
            if any(k in m.lower() for k in _HIGH_RISK_KEYWORDS)
        ]
        if high_risk_sigs:
            importance = _IMPORTANCE_HIGH
            parts.append(f"계약변경: {', '.join(sorted(high_risk_sigs))}")

        # MEDIUM: 새 클래스/메서드, 일반 시그니처 변경
        if importance == _IMPORTANCE_LOW:
            if added_classes:
                importance = _IMPORTANCE_MEDIUM
                parts.append(f"새클래스: {', '.join(sorted(added_classes))}")
            if added_methods:
                importance = _IMPORTANCE_MEDIUM
                parts.append(f"새메서드: {', '.join(sorted(added_methods))}")
            if changed_sigs - set(high_risk_sigs):
                importance = _IMPORTANCE_MEDIUM
                parts.append(f"시그니처변경: {', '.join(sorted(changed_sigs - set(high_risk_sigs)))}")

        # LOW: 요청 키워드만 기록
        if not parts:
            parts.append(self._summarize_request(request))

        return {
            'step': self._step,
            'importance': importance,
            'delta': " | ".join(parts)
        }

    # ─── 프롬프트 구성 ──────────────────────────────────────────────────────────

    def _build_prompt(self, current_code: str, modification_request: str) -> str:
        """
        의미론적 계약을 맨 앞에 배치하고, 중요도 가중 Delta를 중간에,
        수정 요청을 맨 끝에 배치한다 (Lost in the Middle 전략).

        Delta는 중요도 순으로 정렬하여 HIGH 항목을 먼저 노출한다.
        """
        # Layer 2: 중요도 순 정렬 (HIGH → MEDIUM → LOW), 최근 8개 이내
        delta_section = ""
        if self.weighted_deltas:
            importance_order = {_IMPORTANCE_HIGH: 0, _IMPORTANCE_MEDIUM: 1, _IMPORTANCE_LOW: 2}
            recent = self.weighted_deltas[-8:]
            sorted_deltas = sorted(recent, key=lambda d: importance_order[d['importance']])

            history_lines = []
            for d in sorted_deltas:
                marker = "⚠️" if d['importance'] == _IMPORTANCE_HIGH else (
                    "→" if d['importance'] == _IMPORTANCE_MEDIUM else "·"
                )
                history_lines.append(f"{marker} [수정{d['step']}] {d['delta']}")

            delta_section = "\n\n## 변경 이력 (중요도 순)\n" + "\n".join(history_lines)

        return f"""## 의미론적 계약 (step0 기준 — 절대 깨지 말 것)
{self.semantic_contracts}{delta_section}

---

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**의미론적 계약의 타입·상태·의존성을 유지하면서** 수정 요청을 구현하세요.
완전한 수정된 코드를 작성하세요."""

    # ─── 유틸리티 ───────────────────────────────────────────────────────────────

    def _get_method_sigs(self, tree: ast.AST) -> Dict[str, Tuple]:
        result = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = tuple(a.arg for a in item.args.args)
                        result[f"{node.name}.{item.name}"] = params
        return result

    def _get_class_names(self, tree: ast.AST) -> Set[str]:
        return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

    def _get_type_annotations(self, tree: ast.AST) -> Dict[str, str]:
        result = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        key = f"{node.name}.{item.target.id}"
                        result[key] = ast.unparse(item.annotation)
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in item.args.args[1:]:
                            if arg.annotation:
                                key = f"{node.name}.{item.name}.{arg.arg}"
                                result[key] = ast.unparse(arg.annotation)
        return result

    def _get_enum_classes(self, tree: ast.AST) -> Set[str]:
        result = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id == 'Enum') or \
                       (isinstance(base, ast.Attribute) and base.attr == 'Enum'):
                        result.add(node.name)
        return result

    def _summarize_request(self, request: str) -> str:
        words = re.findall(r'[가-힣a-zA-Z_]{2,}', request)
        return " ".join(words[:8]) if words else request[:60]
