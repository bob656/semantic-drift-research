"""상태 문서 기반 에이전트 - Spec/Plan/Constraints 활용"""
from typing import Any
from .base_agent import BaseAgent

class StateDocAgent(BaseAgent):
    """상태 문서를 유지하며 작업하는 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        self.spec_doc = ""
        self.plan_doc = ""
        self.constraints_doc = ""

    def solve_initial(self, task: str) -> str:
        """상태 문서 생성 후 초기 문제 해결"""
        self._initialize_state_docs(task)
        return self._generate_code_with_statedoc(task)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """상태 문서 참조하여 코드 수정"""
        self._update_plan_doc(modification_request)
        return self._modify_with_statedoc(current_code, modification_request)

    def _initialize_state_docs(self, task: str):
        """초기 상태 문서 생성"""
        # Spec.md 생성 (요구사항 명세)
        spec_prompt = f"""다음 요구사항의 상세한 명세서를 작성하세요:

요구사항: {task}

명세서에 포함할 내용:
1. 핵심 기능 목록
2. 데이터 구조 정의
3. 주요 제약조건
4. 예외 처리 규칙

간결하고 명확하게 작성하세요."""

        self.spec_doc = self.call_llm(spec_prompt,
            "당신은 소프트웨어 명세서 작성 전문가입니다.")

        # Constraints.md 생성 (불변 제약조건)
        self.constraints_doc = """# 절대 제약조건 (Constraints.md)

## API 계약 보존
- 기존 public 메서드 이름과 시그니처 변경 금지
- 함수명 변경 금지
- 매개변수 순서 변경 금지
- 반환 타입 변경 금지

## 코드 품질 기준
- 타입 힌트 사용 권장
- Docstring 작성 권장
- 예외 발생 시 명시적 raise (None 반환 금지)
- PEP 8 스타일 가이드 준수

## 기능 보존 원칙
- 기존 기능 파괴 절대 금지
- 모든 기존 테스트 케이스 통과 필수
- 하위 호환성 유지"""

        # Plan.md 초기화 (동적 계획)
        self.plan_doc = f"""# 개발 계획 (Plan.md)

## 현재 단계: 초기 구현
- [ ] 기본 클래스 구조 설계
- [ ] 핵심 로직 구현
- [ ] 기본 테스트 케이스 작성

## 완료된 작업
- [x] 요구사항 분석 완료: {task[:100]}...
- [x] 명세서 작성 완료

## 향후 수정 계획
(수정 요청에 따라 동적으로 업데이트됩니다)"""

    def _generate_code_with_statedoc(self, task: str) -> str:
        """상태 문서 참조하여 코드 생성"""
        system_prompt = """당신은 명세서와 제약조건을 엄격히 준수하는 개발자입니다.
주어진 문서들을 반드시 참조하여 코드를 작성하세요."""

        prompt = f"""## 명세서 (Spec.md)
{self.spec_doc}

## 제약조건 (Constraints.md)
{self.constraints_doc}

## 개발 계획 (Plan.md)
{self.plan_doc}

위 문서들을 기반으로 다음 요구사항을 구현하세요:

요구사항: {task}

**중요 지침**:
- Constraints.md의 모든 제약조건을 반드시 준수하세요
- Spec.md의 요구사항을 정확히 구현하세요
- Plan.md의 단계를 따라 구현하세요
- 완전한 실행 가능한 코드를 작성하세요"""

        response = self.call_llm(prompt, system_prompt)
        return self.extract_code(response)

    def _modify_with_statedoc(self, current_code: str, modification_request: str) -> str:
        """제약조건을 체크하며 코드 수정"""
        system_prompt = """당신은 상태 문서를 엄격히 준수하는 개발자입니다.
기존 기능을 절대 파괴하지 말고 새로운 기능만 추가하세요."""

        prompt = f"""## 명세서 (Spec.md)
{self.spec_doc}

## 제약조건 (Constraints.md)
{self.constraints_doc}

## 현재 계획 (Plan.md)
{self.plan_doc}

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**중요 지침**:
- Constraints.md의 모든 제약조건을 반드시 준수하세요
- 기존 메서드 시그니처를 변경하지 마세요
- 기존 기능을 절대 파괴하지 마세요
- 요청된 기능만 추가하세요
- 완전한 수정된 코드를 작성하세요"""

        response = self.call_llm(prompt, system_prompt)
        return self.extract_code(response)

    def _update_plan_doc(self, modification_request: str):
        """Plan.md를 수정 요청에 따라 업데이트"""
        update_prompt = f"""현재 개발 계획:
{self.plan_doc}

새로운 수정 요청: {modification_request}

위 계획을 업데이트하세요.
- 완료된 항목은 [x]로 표시하세요
- 새로운 수정 요청을 할 일 목록에 추가하세요
- 간결하게 유지하세요"""

        self.plan_doc = self.call_llm(update_prompt,
            "당신은 프로젝트 계획 관리 전문가입니다.")
