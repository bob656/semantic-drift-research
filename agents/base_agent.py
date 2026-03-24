"""기본 에이전트 클래스 - 모든 에이전트의 공통 기능"""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BaseAgent:
    """모든 에이전트의 기본 클래스"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        self.model = model
        self.client = client
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.interaction_log: List[Dict[str, Any]] = []

    def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Ollama API 호출 및 로깅"""
        start_time = time.time()

        try:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                }
            )

            result = response['message']['content']
            duration = time.time() - start_time

            # 상호작용 로그 저장 (디버깅 및 분석용)
            self.interaction_log.append({
                'timestamp': datetime.now().isoformat(),
                'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                'system_preview': system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt,
                'response_preview': result[:300] + "..." if len(result) > 300 else result,
                'duration': duration,
                'success': True
            })

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM 호출 실패: {e}")

            self.interaction_log.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'duration': duration,
                'success': False
            })

            return f"ERROR: {str(e)}"

    def extract_code(self, response: str) -> str:
        """응답에서 Python 코드 추출"""
        # ```python ... ``` 패턴 우선 검색
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        # 일반 ``` ... ``` 패턴 검색
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        # 코드 블록이 없으면 전체 응답 반환
        return response.strip()

    def solve_initial(self, task: str) -> str:
        """초기 문제 해결 (서브클래스에서 구현)"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """코드 수정 (서브클래스에서 구현)"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
