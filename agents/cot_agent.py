"""
cot_agent.py — CoT(Chain of Thought) 추론 단계가 추가된 StateDoc 에이전트

## 설계 동기

StateDocAgent의 실험 결과, 추상 문서(Spec/Plan/Constraints)만으로는
LLM의 구현 재해석을 막지 못한다는 것이 확인됐다.

  실패 패턴: Spec에 "items: List[Item]"이라고 적혀 있어도
             LLM이 add_order를 구현할 때 (item_name, quantity) 튜플로 해석 →
             Order.calculate_total()의 item.price 접근과 충돌 → 코드 내부 불일치

## CoT 해결 전략

수정 요청을 받으면 **코드 생성 전** 별도 LLM 호출로 명시적 추론을 수행한다.

  추론 포함 항목:
    1. 현재 코드의 구체적 데이터 타입과 필드
    2. 변경 금지 메서드 시그니처
    3. 이번 수정의 변경 범위 (추가할 것 vs 절대 바꾸면 안 될 것)
    4. 기존 타입과 새 기능 간의 일관성 체크

  이 추론 결과를 코드 생성 프롬프트에 "사전 분석"으로 포함시켜
  LLM이 기존 구현 세부사항을 재해석하지 못하도록 앵커링한다.

## StateDocAgent와의 차이

  StateDoc  → 문서 + 현재 코드 + 수정 요청 → 코드 생성
  CoTDoc    → 문서 + 현재 코드 + 수정 요청 → [CoT 추론] → 추론 결과 포함 → 코드 생성
             (LLM 호출이 수정당 1회 추가)

LLM 호출 횟수:
  BaselineAgent: 수정당 1회
  StateDocAgent: 수정당 2회 (plan 업데이트 + 코드 생성)
  CoTDocAgent:   수정당 3회 (CoT 분석 + plan 업데이트 + 코드 생성)
"""
from typing import Any
from .base_agent import BaseAgent


class CoTDocAgent(BaseAgent):
    """CoT 추론 단계가 추가된 StateDoc 에이전트"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)

        # StateDocAgent와 동일한 3개 문서 유지
        self.spec_doc = ""
        self.plan_doc = ""
        self.constraints_doc = ""

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial(self, task: str) -> str:
        """초기 과제: 문서 초기화 후 코드 생성 (CoT 불필요 — 기존 코드 없음)"""
        self._initialize_state_docs(task)
        return self._generate_code_with_docs(task)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        수정 요청 처리 흐름:
          1. _cot_analyze()  → 현재 코드의 구체적 타입/시그니처/변경 범위 추론
          2. _update_plan()  → Plan.md 갱신
          3. _generate_modified_code() → CoT 분석 결과를 앵커로 삼아 코드 생성
        """
        cot_analysis = self._cot_analyze(current_code, modification_request)
        self._update_plan(modification_request, cot_analysis)
        return self._generate_modified_code(current_code, modification_request, cot_analysis)

    # ─── 초기화 ────────────────────────────────────────────────────────────────

    def _initialize_state_docs(self, task: str):
        """StateDocAgent와 동일한 방식으로 3개 문서 초기화"""
        spec_prompt = f"""다음 요구사항의 상세한 명세서를 작성하세요:

요구사항: {task}

명세서에 포함할 내용:
1. 핵심 기능 목록
2. 데이터 구조 정의 (클래스명, 필드명, 타입 포함)
3. 주요 메서드 시그니처
4. 제약조건 및 예외 처리 규칙

간결하고 정확하게 작성하세요."""

        self.spec_doc = self.call_llm(
            spec_prompt, "당신은 소프트웨어 명세서 작성 전문가입니다.")

        self.constraints_doc = """# 절대 제약조건 (Constraints.md)

## API 계약 보존
- 기존 public 메서드 이름과 시그니처 변경 금지
- 기존 데이터 클래스의 필드 타입 변경 금지
- 매개변수 순서 변경 금지
- 반환 타입 변경 금지

## 타입 일관성
- 한 번 List[Item]으로 정의된 items는 튜플 리스트로 변경 불가
- 한 번 정의된 클래스 필드의 접근 방식 변경 금지 (item.price는 item['price']로 바꾸지 말 것)

## 기능 보존 원칙
- 기존 기능 파괴 절대 금지
- 모든 기존 메서드는 이전과 동일하게 동작해야 함
- 새 기능 추가만 허용, 기존 로직 변경은 명시적으로 요청된 경우만 허용"""

        self.plan_doc = f"""# 개발 계획 (Plan.md)

## 완료된 작업
- [x] 요구사항 분석: {task[:100]}...
- [x] 명세서 작성

## 향후 수정 계획
(수정 요청에 따라 동적으로 업데이트)"""

    # ─── 초기 코드 생성 ─────────────────────────────────────────────────────────

    def _generate_code_with_docs(self, task: str) -> str:
        """초기 코드: 3개 문서를 참조하여 생성"""
        system_prompt = "당신은 명세서와 제약조건을 엄격히 준수하는 Python 개발자입니다."

        prompt = f"""## 명세서 (Spec.md)
{self.spec_doc}

## 제약조건 (Constraints.md)
{self.constraints_doc}

## 개발 계획 (Plan.md)
{self.plan_doc}

위 문서들을 기반으로 다음 요구사항을 구현하세요:

요구사항: {task}

완전한 실행 가능한 Python 코드를 작성하세요."""

        response = self.call_llm(prompt, system_prompt)
        return self.extract_code(response)

    # ─── CoT 추론 (핵심) ────────────────────────────────────────────────────────

    def _cot_analyze(self, current_code: str, modification_request: str) -> str:
        """
        코드 수정 전 명시적 추론 단계.

        LLM이 다음을 순서대로 분석하게 강제한다:
          1. 현재 코드의 구체적 데이터 구조 (타입 포함)
          2. 변경이 금지된 메서드 시그니처
          3. 이번 수정의 변경 범위 결정
          4. 타입 일관성 확인

        이 추론 결과가 코드 생성 프롬프트의 "앵커"가 된다.
        LLM이 추론 단계에서 "Item(name, price, quantity) 객체"라고 명시하면,
        코드 생성 단계에서 튜플로 재해석할 가능성이 크게 낮아진다.
        """
        prompt = f"""현재 코드를 분석하여 수정 계획을 수립하세요.

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

다음 항목을 **순서대로** 명시적으로 분석하세요:

### 분석 1: 현재 데이터 구조
코드에 정의된 모든 클래스와 그 필드를 정확한 타입과 함께 나열하세요.
예: `Item(name: str, price: float, quantity: int)` — dataclass

### 분석 2: 변경 금지 메서드 시그니처
현재 코드에 있는 핵심 메서드의 정확한 시그니처를 나열하세요.
예: `add_order(self, order_id: int, items: List[Item]) -> None`

### 분석 3: 변경 범위 결정
이번 수정 요청에서:
- **추가할 것**: (새 클래스, 새 메서드, 새 필드)
- **변경하면 안 될 것**: (기존 시그니처, 기존 타입, 기존 로직)

### 분석 4: 타입 일관성 확인
새 기능에서 기존 데이터 타입(Item 객체 등)을 일관되게 사용하고 있는지 확인하세요.
특히: 기존 items가 List[Item]이면 새 코드에서도 반드시 List[Item]을 사용해야 합니다.

### 분석 5: 구체적 구현 계획
변경 사항을 3-5단계로 나열하세요."""

        return self.call_llm(
            prompt,
            "당신은 코드 분석 전문가입니다. 추상적 설명 대신 구체적 타입과 시그니처를 명시하세요.")

    # ─── Plan 업데이트 ──────────────────────────────────────────────────────────

    def _update_plan(self, modification_request: str, cot_analysis: str):
        """CoT 분석 결과를 반영하여 Plan.md 갱신"""
        prompt = f"""현재 개발 계획:
{self.plan_doc}

새로운 수정 요청: {modification_request}

사전 분석 결과 요약:
{cot_analysis[:500]}...

위 계획을 업데이트하세요.
- 완료된 항목은 [x]로 표시
- 새로운 수정 항목 추가
- 간결하게 유지"""

        self.plan_doc = self.call_llm(
            prompt, "당신은 프로젝트 계획 관리 전문가입니다.")

    # ─── 코드 생성 (CoT 앵커 포함) ──────────────────────────────────────────────

    def _generate_modified_code(self, current_code: str,
                                modification_request: str,
                                cot_analysis: str) -> str:
        """
        CoT 분석 결과를 앵커로 삼아 수정된 코드를 생성한다.

        프롬프트 구조:
          [Spec.md] + [Constraints.md] + [Plan.md]
          + [CoT 분석 결과 — 기존 타입/시그니처 명시]
          + [현재 코드]
          + [수정 요청]

        CoT 분석이 "기존 items는 List[Item] 타입"이라고 명시하기 때문에
        LLM이 코드 생성 시 튜플로 재해석할 가능성이 낮아진다.
        """
        system_prompt = """당신은 사전 분석 결과를 정확히 따르는 Python 개발자입니다.
분석에서 확인된 기존 타입과 시그니처를 절대 변경하지 마세요."""

        prompt = f"""## 명세서 (Spec.md)
{self.spec_doc}

## 제약조건 (Constraints.md)
{self.constraints_doc}

## 현재 계획 (Plan.md)
{self.plan_doc}

## 사전 분석 결과 (CoT Analysis) ← 이 분석을 반드시 따르세요
{cot_analysis}

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**위 사전 분석에서 확인된 기존 타입과 시그니처를 그대로 유지하면서**
수정 요청만 구현하세요. 완전한 수정된 코드를 작성하세요."""

        response = self.call_llm(prompt, system_prompt)
        return self.extract_code(response)
