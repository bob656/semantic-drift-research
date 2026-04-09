"""
agents.py — 수치 계약 보존 실험용 에이전트

## 두 가지 에이전트 비교

BaselineAgent:
  - 상태 문서 없음
  - 매 수정 요청을 독립적으로 처리
  - 수치 상수가 무엇인지 프롬프트에 명시되지 않음

NumericContractAgent:
  - step0에서 수치 계약을 추출하여 저장
  - 매 수정 시 "이 수치는 절대 변경 금지" 섹션을 프롬프트에 포함
  - Science China 2025 "Constant Value Error" 문제에 직접 대응

## 논문 연결

Science China Information Sciences (2025):
  "Constant Value Error — 수치 상수를 잘못 변경하는 오류가 GPT-4에서도 가장 빈번"
  → BaselineAgent가 이 문제를 재현
  → NumericContractAgent가 명시적 수치 고정으로 개선
"""
import ast
import re
import sys
import os
from typing import Any, Dict, List, Optional

# 부모 디렉터리의 BaseAgent 재사용
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)
from agents.base_agent import BaseAgent


class BaselineAgent(BaseAgent):
    """
    상태 문서 없는 기본 에이전트.
    수치 상수에 대한 명시적 안내 없이 수정 요청만 전달한다.
    """

    def solve_initial(self, task: str) -> str:
        response = self.call_llm(
            f"다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:\n\n{task}",
            "당신은 Python 개발자입니다. 타입 힌트를 사용하여 구현하세요."
        )
        return self.extract_code(response)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        prompt = (
            f"다음 코드를 수정 요청에 맞게 변경하세요.\n\n"
            f"## 수정 요청\n{modification_request}\n\n"
            f"## 현재 코드\n```python\n{current_code}\n```\n\n"
            "완전한 Python 코드를 반환하세요."
        )
        response = self.call_llm(prompt,
            "당신은 Python 개발자입니다. 수정 요청을 구현하세요.")
        return self.extract_code(response)

    def modify_code_with_syntax_retry(self, current_code: str,
                                       modification_request: str) -> str:
        code = self.modify_code(current_code, modification_request)
        try:
            ast.parse(code)
            return code
        except SyntaxError:
            retry = self.call_llm(
                f"다음 코드에 문법 오류가 있습니다. 수정하세요:\n```python\n{code}\n```",
                "Python 문법 오류만 수정하고 완전한 코드를 반환하세요.")
            return self.extract_code(retry)


class NumericContractAgent(BaseAgent):
    """
    수치 계약을 명시적으로 고정하는 에이전트.

    step0에서 수치 상수를 추출 → 이후 모든 수정 시 프롬프트에
    "절대 변경 금지 수치 목록"을 포함시킨다.

    수치 추출 전략:
      1. AST로 모듈/클래스 수준 상수 추출
      2. 정규식으로 대문자 변수명 패턴 탐지
      3. 시나리오의 known_contracts와 교차 확인
    """

    def __init__(self, model: str, client: Any,
                 known_contracts: Optional[Dict[str, float]] = None,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        # 시나리오에서 사전 정의된 수치 계약 (정답 값)
        self.known_contracts: Dict[str, float] = known_contracts or {}
        # 실제 코드에서 추출한 수치 계약 저장소
        self.pinned_contracts: Dict[str, str] = {}  # {name: "name = value (설명)"}
        self.contract_log: List[Dict] = []

    def solve_initial(self, task: str) -> str:
        response = self.call_llm(
            f"다음 요구사항을 만족하는 완전한 Python 코드를 작성하세요:\n\n{task}",
            "당신은 Python 개발자입니다. 타입 힌트를 사용하여 구현하세요."
        )
        code = self.extract_code(response)

        # step0 코드에서 수치 계약 추출 및 고정
        self._extract_and_pin_contracts(code)
        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        prompt = self._build_prompt(current_code, modification_request)
        response = self.call_llm(prompt,
            "당신은 Python 개발자입니다.\n"
            "[고정 수치 계약] 섹션의 값은 어떤 경우에도 변경하지 마세요.\n"
            "완전한 Python 코드를 반환하세요.")
        new_code = self.extract_code(response)

        # 수정 후 수치 변화 감지 → 로그 기록
        self._log_contract_state(new_code, len(self.contract_log) + 1)
        return new_code

    def modify_code_with_syntax_retry(self, current_code: str,
                                       modification_request: str) -> str:
        code = self.modify_code(current_code, modification_request)
        try:
            ast.parse(code)
            return code
        except SyntaxError:
            retry = self.call_llm(
                f"다음 코드에 문법 오류가 있습니다. 수정하세요:\n```python\n{code}\n```",
                "Python 문법 오류만 수정하고 완전한 코드를 반환하세요.")
            return self.extract_code(retry)

    # ── 수치 계약 추출 ────────────────────────────────────────────

    def _extract_and_pin_contracts(self, code: str) -> None:
        """step0 코드에서 수치 상수를 추출하여 pinned_contracts에 저장"""
        extracted = {}

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (isinstance(target, ast.Name) and
                                isinstance(node.value, ast.Constant) and
                                isinstance(node.value.value, (int, float))):
                            extracted[target.id] = node.value.value
        except SyntaxError:
            pass

        # known_contracts와 교차 확인하여 고정 목록 구성
        for name, expected in self.known_contracts.items():
            variants = self._name_variants(name)
            for variant in variants:
                if variant in extracted:
                    val = extracted[variant]
                    self.pinned_contracts[name] = (
                        f"{variant} = {val}  "
                        f"({'✓ 일치' if abs(val - expected) < 1e-9 else f'⚠ 기대: {expected}'})"
                    )
                    break
            else:
                # 코드에서 못 찾았어도 known_contracts 값으로 고정
                self.pinned_contracts[name] = f"{name} = {expected}  (초기값 기준)"

    def _build_prompt(self, current_code: str, modification_request: str) -> str:
        pinned_section = "\n".join(
            f"  - {line}" for line in self.pinned_contracts.values()
        ) or "  (없음)"

        return (
            f"## 수정 요청\n{modification_request}\n\n"
            f"## [고정 수치 계약] — 아래 값은 절대 변경 금지\n"
            f"{pinned_section}\n\n"
            f"## 현재 코드\n```python\n{current_code}\n```\n\n"
            "고정 수치 계약을 유지하면서 수정 요청을 구현하세요. "
            "완전한 Python 코드를 반환하세요."
        )

    def _log_contract_state(self, code: str, step: int) -> None:
        """수정 후 수치 계약 상태를 로그에 기록"""
        extracted = self._extract_raw_values(code)
        entry = {'step': step, 'contracts': {}}
        for name, expected in self.known_contracts.items():
            actual = extracted.get(name)
            entry['contracts'][name] = {
                'expected': expected,
                'actual': actual,
                'preserved': actual is not None and abs(actual - expected) < 1e-9,
            }
        self.contract_log.append(entry)

    def _extract_raw_values(self, code: str) -> Dict[str, float]:
        """코드에서 이름→값 매핑 추출"""
        found = {}
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (isinstance(target, ast.Name) and
                                isinstance(node.value, ast.Constant) and
                                isinstance(node.value.value, (int, float))):
                            found[target.id] = float(node.value.value)
        except SyntaxError:
            pass

        # 정규식 보완
        for name, _ in self.known_contracts.items():
            if name not in found:
                for variant in self._name_variants(name):
                    m = re.search(
                        rf'\b{re.escape(variant)}\s*=\s*([0-9]+(?:\.[0-9]+)?)',
                        code, re.IGNORECASE)
                    if m:
                        found[name] = float(m.group(1))
                        break
        return found

    def _name_variants(self, name: str) -> List[str]:
        upper = name
        lower = name.lower()
        parts = name.split('_')
        camel = parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
        pascal = ''.join(p.capitalize() for p in parts)
        return [upper, lower, camel, pascal]
