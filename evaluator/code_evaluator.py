"""LLM 기반 코드 평가 시스템"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

class CodeEvaluator:
    """LLM을 활용한 코드 품질 평가"""

    def __init__(self, model: str, client: Any):
        self.model = model
        self.client = client

    def evaluate(self, code: str, task: str) -> float:
        """코드 평가 (0-10점 척도)"""
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
                        'content': '당신은 엄격하고 객관적인 코드 평가자입니다. 숫자만 출력하세요.'
                    },
                    {'role': 'user', 'content': eval_prompt}
                ],
                options={'temperature': 0.1, 'num_predict': 64}
            )

            result_text = response['message']['content'].strip()

            # 숫자 추출 (정규식 사용)
            numbers = re.findall(r'\d+\.?\d*', result_text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(10.0, score))
            else:
                logger.warning(f"평가 결과에서 숫자를 찾을 수 없음: {result_text}")
                return 5.0

        except Exception as e:
            logger.error(f"코드 평가 실패: {e}")
            return 5.0
