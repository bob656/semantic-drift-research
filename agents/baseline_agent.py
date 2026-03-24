"""베이스라인 에이전트 - 대화 히스토리만 사용"""
from typing import Any, List, Dict
from .base_agent import BaseAgent

class BaselineAgent(BaseAgent):
    """대화 히스토리만 사용하는 베이스라인 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        self.conversation_history: List[Dict[str, str]] = []

    def solve_initial(self, task: str) -> str:
        """초기 문제 해결"""
        system_prompt = """당신은 Python 프로그래밍 전문가입니다.
주어진 요구사항에 맞는 완전한 Python 코드를 작성하세요.
코드만 출력하고 불필요한 설명은 생략하세요."""
        prompt = f"""다음 요구사항을 만족하는 Python 코드를 작성하세요:
{task}
완전한 실행 가능한 코드를 작성하세요."""
        response = self.call_llm(prompt, system_prompt)
        code = self.extract_code(response)

        # 대화 히스토리 저장
        self.conversation_history.append({'role': 'user', 'content': task})
        self.conversation_history.append({'role': 'assistant', 'content': code})

        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """기존 코드 수정 (컨텍스트 기반)"""
        context = self._build_context()

        system_prompt = """당신은 기존 코드를 수정하는 전문가입니다.
기존 기능을 유지하면서 새로운 요구사항을 추가하세요."""

        prompt = f"""이전 대화 요약:
{context}

현재 코드:
```python
{current_code}
```

수정 요청: {modification_request}

위 코드를 수정하여 요청사항을 구현하세요. 기존 기능을 유지하면서 새로운 기능을 추가하세요.
완전한 수정된 코드를 작성하세요."""

        response = self.call_llm(prompt, system_prompt)
        modified_code = self.extract_code(response)

        # 대화 히스토리 업데이트
        self.conversation_history.append({'role': 'user', 'content': modification_request})
        self.conversation_history.append({'role': 'assistant', 'content': modified_code})

        return modified_code

    def _build_context(self) -> str:
        """대화 히스토리를 컨텍스트 문자열로 변환"""
        context_parts = []
        # 최근 6개 항목만 사용 (컨텍스트 길이 제한)
        for entry in self.conversation_history[-6:]:
            role = "사용자" if entry['role'] == 'user' else "어시스턴트"
            content = entry['content']
            if len(content) > 300:
                content = content[:300] + "..."
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)
