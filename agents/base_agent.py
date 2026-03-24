"""
base_agent.py — 모든 에이전트의 공통 기반 클래스

BaselineAgent와 StateDocAgent 모두 이 클래스를 상속합니다.
공통으로 필요한 두 가지 기능을 여기서 구현합니다:
  1. LLM 호출 (call_llm)
  2. 응답에서 코드 블록 추출 (extract_code)

실제 코드 생성/수정 전략은 서브클래스에서 각자 구현합니다.
"""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BaseAgent:
    """모든 에이전트의 기본 클래스"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        """
        Parameters
        ----------
        model       : Ollama 모델 이름 (예: "qwen2.5-coder:7b")
        client      : ollama.Client 인스턴스 — 원격 서버 연결 정보를 담고 있음
        temperature : 출력 다양성 조절 (0.0=결정론적, 1.0=창의적)
                      현재 0.1로 설정되어 있어 거의 같은 결과를 반복 생성함
                      → 실험 독립성 문제의 원인 (explore.md 참고)
        max_tokens  : LLM이 한 번에 생성할 최대 토큰 수
        """
        self.model = model
        self.client = client
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 모든 LLM 호출 기록을 저장하는 리스트
        # 실험 후 JSON에 total_interactions 항목으로 저장됨
        self.interaction_log: List[Dict[str, Any]] = []

    def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Ollama 서버에 메시지를 보내고 응답 텍스트를 반환합니다.

        메시지 구조:
          [system]  → LLM의 역할/페르소나 설정 (선택)
          [user]    → 실제 요청 프롬프트

        호출 결과는 항상 interaction_log에 기록되며,
        오류 발생 시 "ERROR: ..." 문자열을 반환합니다 (예외를 밖으로 던지지 않음).
        """
        start_time = time.time()

        try:
            # system_prompt가 있을 때만 system 메시지를 포함
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,  # Ollama의 최대 생성 토큰 옵션명
                }
            )

            # Ollama 응답 구조: response['message']['content']
            result = response['message']['content']
            duration = time.time() - start_time

            # 로그에는 전체 내용 대신 미리보기만 저장 (메모리 절약)
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
            # 연결 실패, 모델 없음 등 → 실험이 멈추지 않도록 에러 문자열 반환
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
        """
        LLM 응답 텍스트에서 Python 코드 블록만 추출합니다.

        LLM은 보통 코드를 마크다운 코드 블록으로 감싸서 반환합니다:
          ```python
          def foo(): ...
          ```

        우선순위:
          1. ```python ... ``` 블록 (언어 명시된 경우)
          2. ``` ... ```       블록 (언어 미명시)
          3. 코드 블록 없으면 응답 전체를 그대로 반환
        """
        # 1순위: ```python 으로 시작하는 블록
        if "```python" in response:
            start = response.find("```python") + 9  # "```python" 길이 = 9
            end = response.find("```", start)        # 닫는 ```의 위치
            if end != -1:
                return response[start:end].strip()

        # 2순위: 언어 표시 없는 일반 코드 블록
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        # 코드 블록이 아예 없는 경우 (LLM이 그냥 코드만 바로 쓴 경우)
        return response.strip()

    def solve_initial(self, task: str) -> str:
        """
        초기 과제를 받아 코드를 처음 작성합니다.
        서브클래스(BaselineAgent, StateDocAgent)에서 반드시 구현해야 합니다.
        """
        raise NotImplementedError("서브클래스에서 구현해야 합니다")

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        기존 코드에 수정 요청을 반영합니다.
        서브클래스(BaselineAgent, StateDocAgent)에서 반드시 구현해야 합니다.

        Parameters
        ----------
        current_code         : 이전 단계까지 완성된 코드
        modification_request : 이번 단계에서 추가/변경할 내용
        """
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
