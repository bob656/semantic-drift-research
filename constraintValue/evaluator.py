"""
evaluator.py — 수치 계약 보존율 측정

## 측정 방식

코드에서 수치 상수를 직접 추출하여 기대값과 비교한다.
LLM 채점이 아닌 정적 분석 기반이므로 완전히 객관적이다.

## 측정 항목

각 수정 단계 후 다음 5개 수치가 원래 값과 동일한지 확인:
  INTEREST_RATE     0.025
  LATE_FEE          5000
  MAX_INSTALLMENTS  36
  MIN_PAYMENT       10000
  PENALTY_RATE      0.015

점수 = 보존된 수치 수 / 전체 수치 수 * 10  (0~10점)
"""
import ast
import re
from typing import Dict, List, Tuple


# 허용 오차 (부동소수점 비교)
_FLOAT_TOL = 1e-9


class NumericEvaluator:
    """코드에서 수치 상수를 추출하여 기대값과 비교"""

    def __init__(self, contracts: Dict[str, float]):
        """
        Parameters
        ----------
        contracts : {'INTEREST_RATE': 0.025, 'LATE_FEE': 5000, ...}
        """
        self.contracts = contracts

    def evaluate(self, code: str) -> Tuple[float, List[str]]:
        """
        코드에서 수치 상수를 추출하고 보존율을 계산한다.

        Returns
        -------
        score   : 0~10점 (보존된 수치 수 / 전체 * 10)
        details : 각 수치별 결과 메시지 리스트
        """
        found = self._extract_numeric_values(code)
        details = []
        preserved = 0

        for name, expected in self.contracts.items():
            actual = found.get(name)
            if actual is None:
                details.append(f"MISSING  {name}: 코드에서 찾을 수 없음 (기대: {expected})")
            elif abs(actual - expected) < _FLOAT_TOL:
                details.append(f"PRESERVED {name}: {actual} ✓")
                preserved += 1
            else:
                details.append(f"CHANGED  {name}: {actual} (기대: {expected}) ✗")

        score = preserved / len(self.contracts) * 10
        return score, details

    def _extract_numeric_values(self, code: str) -> Dict[str, float]:
        """
        코드에서 수치 상수를 추출한다.

        탐지 전략 (우선순위 순):
          1. 클래스/모듈 수준 상수 할당: INTEREST_RATE = 0.025
          2. 딕셔너리 리터럴: {'INTEREST_RATE': 0.025}
          3. 함수/메서드 내 변수: interest_rate = 0.025
          4. 비교/연산식: if months > 36
        """
        found = {}

        # 전략 1, 3: 이름 = 값 패턴 (대소문자 무관)
        for name in self.contracts:
            # 변수명 변형들 (INTEREST_RATE, interest_rate, interestRate 등)
            variants = self._name_variants(name)
            for variant in variants:
                # 할당 패턴: name = <value>
                pattern = rf'(?<!["\'])\b{re.escape(variant)}\s*=\s*([0-9]+(?:\.[0-9]+)?)'
                match = re.search(pattern, code, re.IGNORECASE)
                if match:
                    try:
                        found[name] = float(match.group(1))
                    except ValueError:
                        pass
                    break

        # 전략 2: 딕셔너리 또는 함수 인자에서 수치 탐지
        # AST로 리터럴 숫자를 수집하여 기대값과 매칭
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 상수 할당 (모듈/클래스 레벨)
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            tname = target.id.upper()
                            if isinstance(node.value, ast.Constant):
                                val = node.value.value
                                if isinstance(val, (int, float)):
                                    # 계약 이름과 매칭
                                    for cname in self.contracts:
                                        if cname.replace('_', '') == tname.replace('_', ''):
                                            found[cname] = float(val)
        except SyntaxError:
            pass

        # 전략 4: 수치값 직접 탐지 (이름 없이 값만 있는 경우)
        # 기대값이 코드에 리터럴로 존재하는지 확인
        for name, expected in self.contracts.items():
            if name not in found:
                # 정수 기대값
                if expected == int(expected):
                    pattern = rf'\b{int(expected)}\b'
                else:
                    pattern = rf'\b{expected}\b'
                if re.search(pattern, code):
                    found[name] = expected  # 값은 맞지만 변수명 불명확 → 보존으로 처리

        return found

    def _name_variants(self, name: str) -> List[str]:
        """INTEREST_RATE → [INTEREST_RATE, interest_rate, interestRate, InterestRate]"""
        upper = name
        lower = name.lower()
        # camelCase 변환
        parts = name.split('_')
        camel = parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
        pascal = ''.join(p.capitalize() for p in parts)
        return [upper, lower, camel, pascal]
