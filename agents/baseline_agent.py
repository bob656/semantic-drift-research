"""
baseline_agent.py — 대화 히스토리만 사용하는 베이스라인 에이전트

이 에이전트는 LLM에게 이전 대화 내용을 요약해서 전달하는 방식으로 작동합니다.
상태 문서(Spec, Plan, Constraints)를 따로 유지하지 않기 때문에,
수정 횟수가 늘어날수록 초기 요구사항을 잊어버릴 가능성이 높습니다.

실험에서 "아무런 보조 장치 없이 순수하게 대화만으로 코딩하면 어떻게 되는가"를
측정하기 위한 비교 기준(control group) 역할을 합니다.
"""
from typing import Any, List, Dict
from .base_agent import BaseAgent


class BaselineAgent(BaseAgent):
    """대화 히스토리만 사용하는 베이스라인 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        # 지금까지 오간 대화를 순서대로 저장하는 리스트
        # 각 항목은 {'role': 'user'|'assistant', 'content': '...'} 형태
        # 단, 실제로 LLM에게는 최근 6개 항목만 전달됨 (_build_context 참고)
        self.conversation_history: List[Dict[str, str]] = []

    def solve_initial(self, task: str) -> str:
        """
        초기 과제를 받아 코드를 처음 작성합니다.

        흐름:
          1. 시스템 프롬프트로 LLM에게 "Python 전문가" 역할 부여
          2. 과제 텍스트를 프롬프트로 전달
          3. 응답에서 코드 블록 추출
          4. 과제와 생성된 코드를 대화 히스토리에 저장
        """
        system_prompt = """당신은 Python 프로그래밍 전문가입니다.
주어진 요구사항에 맞는 완전한 Python 코드를 작성하세요.
코드만 출력하고 불필요한 설명은 생략하세요."""

        prompt = f"""다음 요구사항을 만족하는 Python 코드를 작성하세요:
{task}
완전한 실행 가능한 코드를 작성하세요."""

        response = self.call_llm(prompt, system_prompt)
        code = self.extract_code(response)

        # 이후 수정 단계에서 _build_context()가 이 기록을 참조함
        self.conversation_history.append({'role': 'user', 'content': task})
        self.conversation_history.append({'role': 'assistant', 'content': code})

        return code

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        기존 코드에 수정 요청을 반영합니다.

        흐름:
          1. 지금까지의 대화를 요약한 컨텍스트 문자열 생성
          2. [컨텍스트 + 현재 코드 + 수정 요청]을 하나의 프롬프트로 조합
          3. LLM이 수정된 코드 반환
          4. 이번 수정 요청과 결과를 대화 히스토리에 추가

        한계:
          컨텍스트는 최근 6개 항목만 포함하므로, 수정이 4번 이상 쌓이면
          가장 초기의 요구사항(add_student 등)이 컨텍스트에서 밀려납니다.
          이것이 의미 드리프트 발생 경로입니다.
        """
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

        # 이번 수정 내용도 히스토리에 누적
        self.conversation_history.append({'role': 'user', 'content': modification_request})
        self.conversation_history.append({'role': 'assistant', 'content': modified_code})

        return modified_code

    def _build_context(self) -> str:
        """
        대화 히스토리를 LLM에게 전달할 텍스트로 변환합니다.

        전략:
          - 최근 6개 항목만 사용 (토큰 절약 + LLM 컨텍스트 길이 제한)
          - 각 항목은 300자로 잘라냄 (긴 코드가 통째로 들어가지 않도록)

        예시 출력:
          [사용자]: StudentManager 만들어줘
          [어시스턴트]: class StudentManager: ...
          [사용자]: 점수 기능 추가해줘
          [어시스턴트]: class StudentManager: ... (add_score 포함)
        """
        context_parts = []
        # 히스토리 전체가 아닌 최근 6개만 슬라이싱
        for entry in self.conversation_history[-6:]:
            role = "사용자" if entry['role'] == 'user' else "어시스턴트"
            content = entry['content']
            # 코드가 길면 앞 300자만 전달 (토큰 절약)
            if len(content) > 300:
                content = content[:300] + "..."
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)
