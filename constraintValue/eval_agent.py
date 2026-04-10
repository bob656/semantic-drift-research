"""
eval_agent.py — 수치 계약 검증 평가 에이전트

## 역할

Evaluator는 Generator가 생성한 코드를 보고
"상태 문서(수치 계약)가 실제 코드에서 지켜지고 있는가"를
무자비할 정도로 엄격하게 검증한다.

## 설계 원칙

1. 칭찬 금지 — 오직 위반, 누락, 변경만 보고
2. 수치 일치성 검증 — 소수점까지 정확히 일치해야 통과
3. AI Slop 감지 — 수치가 "관행적으로" 바뀐 경우 (예: 0.025→0.03) 감지
4. 상태 문서와 코드의 불일치 = Semantic Drift로 판정

## 출력 형식

각 수치 계약에 대해:
  [계약명] PASS | 코드 위치 설명
  [계약명] FAIL | 위반 내용 및 실제 값

최종 점수: 0.0 ~ 10.0 (PASS 수 / 전체 계약 수 × 10)
"""
import re
from typing import Any, Dict, List, Tuple
import sys
import os

_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)
from agents.base_agent import BaseAgent


# Evaluator 판정 파싱 패턴 — 대괄호 있음/없음 모두 처리
_VERDICT_PATTERN = re.compile(
    r'\[?([A-Z_0-9]+)\]?\s+(PASS|FAIL)\s*\|\s*(.+?)$',
    re.MULTILINE
)


EVALUATOR_SYSTEM_PROMPT = """당신은 세계 최고의 시니어 소프트웨어 아키텍트이자 수치 계약 검증 전문가입니다.
당신의 목표는 생성된 코드에서 수치 상수(Constant Value)의 오염과 변조를 찾아내는 것입니다.

[평가 원칙]
1. 칭찬 금지: '잘했다'는 말은 생략하고 오직 위반과 오류만 지적하십시오.
2. 수치 일치성 검증: 상태 문서(수치 계약)에 기술된 값이 실제 소스 코드와 소수점까지 100% 일치하는지 대조하십시오.
3. 불일치 = 심각한 드리프트: 값이 다르거나, 변수명만 바뀌었거나, 하드코딩으로 숨겨진 경우 모두 FAIL입니다.
4. 누락도 FAIL: 수치 계약이 코드 어디에도 없으면 FAIL입니다.
5. AI 관성 감지: LLM이 관행적으로 바꾸는 패턴(0.025→0.03, 5000→3000)을 특히 주의하십시오.

[출력 형식 — 반드시 이 형식만 사용]
[계약명] PASS | <코드에서 해당 값이 사용되는 위치 설명>
[계약명] FAIL | <실제 발견된 값 또는 누락 사유>

마지막 줄: SCORE: <통과한 계약 수>/<전체 계약 수>"""


class EvaluatorAgent(BaseAgent):
    """
    수치 계약 검증 평가 에이전트.

    Generator가 생성한 코드를 보고 수치 계약 위반 여부를 판정한다.
    LLM 기반이므로 변수명 변형, 하드코딩, 함수 내 숨겨진 수치까지 탐지 가능.
    """

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1,  # 평가자는 결정론적으로
                 max_tokens: int = 1024):
        super().__init__(model, client, temperature, max_tokens)

    def evaluate(self, code: str,
                 contracts: Dict[str, float],
                 step_index: int,
                 modification_request: str = "") -> Tuple[float, List[str], Dict]:
        """
        코드를 평가하여 수치 계약 보존 점수를 반환한다.

        Parameters
        ----------
        code                 : 평가할 코드
        contracts            : {'INTEREST_RATE': 0.025, ...}
        step_index           : 현재 단계 (0=초기, 1~5=수정)
        modification_request : 이번 수정 요청 (맥락 제공용)

        Returns
        -------
        score    : 0.0 ~ 10.0
        details  : 각 계약별 판정 메시지 리스트
        verdicts : {'INTEREST_RATE': ('PASS'|'FAIL', 설명), ...}
        """
        contract_list = "\n".join(
            f"  {name} = {value}" for name, value in contracts.items()
        )

        context = (f"\n[이번 수정 요청]\n{modification_request[:200]}"
                   if modification_request else "")

        prompt = f"""다음 수치 계약 목록과 Python 코드를 대조하여 각 계약의 준수 여부를 판정하세요.

[수치 계약 목록 — 이 값들이 코드에 정확히 존재해야 합니다]
{contract_list}
{context}

[평가 대상 코드 (step{step_index})]
```python
{code[:3000]}
```

각 계약에 대해 정확히 아래 형식으로만 출력하세요:
[계약명] PASS | <위치 설명>
[계약명] FAIL | <위반 내용>

마지막 줄: SCORE: <통과수>/{len(contracts)}"""

        response = self.call_llm(prompt, EVALUATOR_SYSTEM_PROMPT)

        return self._parse_response(response, contracts)

    def _parse_response(self, response: str,
                        contracts: Dict[str, float]) -> Tuple[float, List[str], Dict]:
        verdicts = {}
        details = []

        for match in _VERDICT_PATTERN.finditer(response):
            name, verdict, reason = match.group(1), match.group(2), match.group(3).strip()
            verdicts[name] = (verdict, reason)

        # 파싱 안 된 계약은 FAIL 처리
        for name in contracts:
            if name not in verdicts:
                verdicts[name] = ('FAIL', '평가자 응답에서 판정 누락')

        pass_count = sum(1 for v, _ in verdicts.values() if v == 'PASS')
        score = pass_count / len(contracts) * 10

        for name, (verdict, reason) in verdicts.items():
            mark = "✓" if verdict == "PASS" else "✗"
            details.append(f"{verdict} {mark} {name} | {reason}")

        return score, details, verdicts
