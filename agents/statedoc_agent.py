"""
statedoc_agent.py — 상태 문서(Spec/Plan/Constraints)를 유지하는 에이전트

이 에이전트가 실험의 핵심 가설을 구현합니다:
  "문서를 항상 들고 다니면 드리프트를 줄일 수 있다"

3개의 문서를 메모리에 유지하며, 코드를 생성하거나 수정할 때마다
해당 문서들을 프롬프트에 포함시킵니다.

  Spec.md        → "이 시스템은 원래 이런 것이다" (초기 생성 후 고정)
  Constraints.md → "이것만은 절대 바꾸지 마라" (하드코딩, 항상 고정)
  Plan.md        → "지금까지 이것들을 완료했다" (수정마다 LLM이 갱신)

BaselineAgent와의 차이:
  Baseline  → 최근 대화 6개만 기억
  StateDoc  → 3개 문서 전체를 항상 전달 (초기 요구사항이 절대 잊혀지지 않음)
"""
from typing import Any
from .base_agent import BaseAgent


class StateDocAgent(BaseAgent):
    """상태 문서를 유지하며 작업하는 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.1, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        # 3개의 상태 문서를 문자열로 메모리에 유지
        self.spec_doc = ""         # 요구사항 명세 (초기 1회 생성 후 불변)
        self.plan_doc = ""         # 작업 진행 계획 (수정마다 업데이트)
        self.constraints_doc = ""  # 절대 지켜야 할 제약 (하드코딩, 불변)

    def solve_initial(self, task: str) -> str:
        """
        초기 과제를 받아 상태 문서를 먼저 만든 뒤 코드를 생성합니다.

        흐름:
          1. _initialize_state_docs() → Spec.md, Constraints.md, Plan.md 생성
          2. _generate_code_with_statedoc() → 3개 문서를 참조하여 코드 작성
        """
        self._initialize_state_docs(task)
        return self._generate_code_with_statedoc(task)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        수정 요청을 받아 Plan.md를 먼저 갱신한 뒤 코드를 수정합니다.

        흐름:
          1. _update_plan_doc() → 이번 수정 요청을 Plan.md에 반영
          2. _modify_with_statedoc() → 3개 문서 + 현재 코드 + 수정 요청 전달
        """
        self._update_plan_doc(modification_request)
        return self._modify_with_statedoc(current_code, modification_request)

    def _initialize_state_docs(self, task: str):
        """
        실험 시작 시 3개의 상태 문서를 초기화합니다.

        Spec.md:
          LLM에게 요구사항 명세서 작성을 요청합니다.
          핵심 기능 목록, 데이터 구조, 제약조건, 예외 처리 규칙을 포함합니다.
          초기 1회만 생성되며 이후 수정되지 않습니다.

        Constraints.md:
          코드로 하드코딩된 불변 규칙입니다. LLM이 생성하지 않습니다.
          "기존 메서드 이름 변경 금지", "기존 기능 파괴 금지" 등
          의미 드리프트를 직접 막는 규칙들이 담겨 있습니다.

        Plan.md:
          현재까지의 작업 진행 상황을 체크리스트 형식으로 관리합니다.
          수정 요청이 들어올 때마다 _update_plan_doc()이 갱신합니다.
        """
        # --- Spec.md: LLM이 요구사항을 명세서로 정리 ---
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

        # --- Constraints.md: 하드코딩된 절대 규칙 (LLM 생성 X) ---
        # 이 규칙들이 StateDocAgent의 핵심 드리프트 방지 장치입니다.
        # 매 수정 프롬프트에 항상 포함되어 LLM에게 강제됩니다.
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

        # --- Plan.md: 초기 체크리스트 (이후 _update_plan_doc이 갱신) ---
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
        """
        3개의 상태 문서를 참조하여 초기 코드를 생성합니다.

        프롬프트 구조:
          [Spec.md 전체] + [Constraints.md 전체] + [Plan.md 전체] + [요구사항]
        """
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
        """
        3개의 상태 문서를 참조하여 코드를 수정합니다.

        프롬프트 구조:
          [Spec.md] + [Constraints.md] + [Plan.md(갱신됨)] + [현재 코드] + [수정 요청]

        Baseline과의 핵심 차이:
          Baseline은 대화 요약만 전달하지만,
          StateDoc은 Spec(원래 요구사항)과 Constraints(불변 규칙)를 항상 포함하여
          LLM이 초기 요구사항을 절대 잊지 못하게 합니다.
        """
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
        """
        새로운 수정 요청을 반영하여 Plan.md를 갱신합니다.

        수정 요청이 들어올 때마다 호출되며,
        LLM에게 현재 Plan.md를 주고 새 항목을 추가하도록 요청합니다.

        예시:
          수정 전 Plan.md: "- [x] 초기 구현 완료"
          수정 후 Plan.md: "- [x] 초기 구현 완료\n- [ ] 점수 기능 추가"

        주의:
          Plan.md 갱신도 LLM 호출이므로 추가 시간이 소요됩니다.
          StateDoc이 Baseline보다 느린 이유 중 하나입니다.
        """
        update_prompt = f"""현재 개발 계획:
{self.plan_doc}

새로운 수정 요청: {modification_request}

위 계획을 업데이트하세요.
- 완료된 항목은 [x]로 표시하세요
- 새로운 수정 요청을 할 일 목록에 추가하세요
- 간결하게 유지하세요"""

        # Plan.md를 LLM이 생성한 새 버전으로 교체
        self.plan_doc = self.call_llm(update_prompt,
            "당신은 프로젝트 계획 관리 전문가입니다.")
