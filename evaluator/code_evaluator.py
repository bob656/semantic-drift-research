"""
code_evaluator.py — LLM 기반 코드 품질 평가

실험에서 에이전트가 생성한 코드를 0~10점으로 채점합니다.
채점자도 동일한 LLM(qwen2.5-coder)이며, 별도의 테스트 코드 실행은 없습니다.

평가 기준 (프롬프트에 명시):
  - 요구사항 충족도 40%: 해당 단계 수정 요청이 구현되었는가
  - 코드 품질        30%: 가독성, 구조, 네이밍
  - 오류 방지        30%: 명백한 버그, 문법 오류

알려진 한계:
  1. "해당 단계 수정 요청만" 기준이므로 이전 단계 기능이 깨져도 감지 못함
     → 드리프트가 발생해도 점수가 떨어지지 않을 수 있음
  2. temperature=0.1 → 동일 코드에 항상 같은 점수 부여 (결정론적)
     → 반복 실험의 독립성이 깨짐

SWT-Bench 적용 시에는 이 클래스를 pytest 실행 기반으로 교체해야 합니다.
(explore.md의 SWT-Bench 가이드 참고)
"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CodeEvaluator:
    """LLM을 활용한 코드 품질 평가"""

    def __init__(self, model: str, client: Any):
        """
        Parameters
        ----------
        model  : 평가에 사용할 LLM 모델 (에이전트와 동일한 모델 사용)
        client : ollama.Client 인스턴스
        """
        self.model = model
        self.client = client

    def evaluate(self, code: str, task: str) -> float:
        """
        주어진 코드를 task 기준으로 0~10점으로 평가합니다.

        Parameters
        ----------
        code : 평가할 Python 코드 문자열
        task : 평가 기준이 되는 요구사항 텍스트
               현재는 "해당 단계의 수정 요청"만 전달됨
               (누적 요구사항으로 바꾸면 드리프트 포착 가능)

        Returns
        -------
        float : 0.0 ~ 10.0 사이의 점수
                LLM 오류 또는 숫자 파싱 실패 시 5.0(중간값) 반환
        """
        eval_prompt = f"""다음 Python 코드가 요구사항을 얼마나 잘 구현했는지 0-10점으로 평가하세요.

요구사항:
{task}

코드:
```python
{code}
```

평가 기준:
- 요구사항 충족도 (40%): 요구된 기능이 정확히 구현되었는가?
- 코드 품질 (30%): 가독성, 구조, 네이밍 등이 우수한가?
- 오류 방지 (30%): 명백한 버그나 문법 오류가 없는가?

중요: 반드시 0에서 10 사이의 숫자만 출력하세요. (예: 7.5) 설명이나 다른 텍스트는 포함하지 마세요."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        # "숫자만 출력"을 강조 — LLM이 설명을 붙이면 파싱이 실패하기 때문
                        'content': '당신은 엄격하고 객관적인 코드 평가자입니다. 숫자만 출력하세요.'
                    },
                    {'role': 'user', 'content': eval_prompt}
                ],
                # 점수 하나만 출력하면 되므로 num_predict를 64로 제한 (속도 향상)
                options={'temperature': 0.1, 'num_predict': 64}
            )

            result_text = response['message']['content'].strip()

            # LLM이 "7.5점입니다" 처럼 텍스트를 섞어 반환할 수 있으므로
            # 정규식으로 첫 번째 숫자만 추출
            numbers = re.findall(r'\d+\.?\d*', result_text)
            if numbers:
                score = float(numbers[0])
                # 혹시 100점 만점으로 채점하는 경우 등을 대비해 0~10으로 강제 클리핑
                return max(0.0, min(10.0, score))
            else:
                logger.warning(f"평가 결과에서 숫자를 찾을 수 없음: {result_text}")
                return 5.0  # 파싱 실패 시 중간값 반환

        except Exception as e:
            # 연결 오류 등 → 실험이 멈추지 않도록 중간값 반환
            logger.error(f"코드 평가 실패: {e}")
            return 5.0
