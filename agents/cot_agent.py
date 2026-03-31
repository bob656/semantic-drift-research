"""
cot_agent.py — Summary 기반 CoT 에이전트 (Lost in the Middle 해결 버전)

## 문제 진단

StateDocAgent 실패 원인:
  1차: 추상 문서 → LLM이 구현 세부사항 재해석 (Item vs 튜플)
  2차: CoT 분석을 프롬프트 중간에 배치 → "Lost in the Middle" 현상으로 무시됨

  기존 프롬프트 구조:
    [Spec.md — 길다]          ← 앞 (잘 읽힘)
    [Constraints.md]
    [Plan.md]
    [CoT 분석 — 핵심!]        ← 중간 (무시됨)
    [현재 코드 — 길다]
    [수정 요청]                ← 끝 (잘 읽힘)

## Summary 해결 전략

LLM이 가장 집중하는 위치(프롬프트 시작)에 핵심 정보를 압축해 배치.

  새 프롬프트 구조:
    [구현 요약 — 짧고 구체적]  ← 시작 (가장 잘 읽힘)
      · 현재 클래스/타입 목록
      · 변경 금지 시그니처 목록
      · 이번에 추가할 것만
    [현재 코드]
    [수정 요청]                ← 끝 (잘 읽힘)

  Spec/Plan/Constraints 같은 긴 문서는 코드 생성 프롬프트에서 제거.
  CoT 분석은 Summary 생성에만 사용하고, 분석 자체는 프롬프트에 포함하지 않음.

LLM 호출 횟수 (수정당):
  BaselineAgent: 1회
  StateDocAgent: 2회 (plan 업데이트 + 코드 생성)
  CoTDocAgent:   2회 (summary 생성 + 코드 생성)  ← plan 업데이트 제거
"""
from typing import Any
from .base_agent import BaseAgent


class CoTDocAgent(BaseAgent):
    """Summary 기반 CoT 에이전트 — Lost in the Middle 해결"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        super().__init__(model, client, temperature, max_tokens)
        # 초기 문서 (초기 코드 생성에만 사용)
        self.spec_doc = ""
        self.constraints_doc = ""

    # ─── 공개 인터페이스 ────────────────────────────────────────────────────────

    def solve_initial(self, task: str) -> str:
        """초기 코드: Spec으로 생성 (CoT 불필요 — 기존 코드 없음)"""
        self._initialize_docs(task)
        return self._generate_initial_code(task)

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        수정 흐름:
          1. _build_summary()  → 현재 코드의 핵심을 짧게 요약 (변경 금지 목록 포함)
          2. _generate_modified_code() → Summary를 프롬프트 맨 앞에 배치하여 코드 생성
        """
        summary = self._build_summary(current_code, modification_request)
        return self._generate_modified_code(current_code, modification_request, summary)

    # ─── 초기화 ────────────────────────────────────────────────────────────────

    def _initialize_docs(self, task: str):
        """초기 Spec 문서 생성 (불변)"""
        self.spec_doc = self.call_llm(
            f"""다음 요구사항의 명세서를 작성하세요:

요구사항: {task}

포함할 내용:
1. 핵심 클래스와 필드 (정확한 타입 포함)
2. 주요 메서드 시그니처
3. 예외 처리 규칙

간결하게 작성하세요.""",
            "당신은 소프트웨어 명세서 작성 전문가입니다.")

        self.constraints_doc = """## 절대 제약
- 기존 public 메서드 이름/시그니처/반환타입 변경 금지
- 기존 데이터 타입 변경 금지 (List[Item]을 튜플 리스트로 바꾸는 등 금지)
- 기존 기능 파괴 금지, 새 기능만 추가"""

    # ─── 초기 코드 생성 ─────────────────────────────────────────────────────────

    def _generate_initial_code(self, task: str) -> str:
        prompt = f"""## 명세서
{self.spec_doc}

## 제약조건
{self.constraints_doc}

요구사항: {task}

완전한 실행 가능한 Python 코드를 작성하세요."""

        return self.extract_code(
            self.call_llm(prompt,
                "당신은 명세서와 제약조건을 준수하는 Python 개발자입니다."))

    # ─── Summary 생성 (핵심 — Lost in the Middle 해결) ─────────────────────────

    def _build_summary(self, current_code: str, modification_request: str) -> str:
        """
        현재 코드를 분석하여 코드 생성에 필요한 핵심 제약을 짧게 요약한다.

        목표: 긴 CoT 분석 대신 5-10줄짜리 압축된 "변경 금지 목록"을 만들어
              프롬프트 맨 앞에 배치함으로써 Lost in the Middle을 방지한다.

        출력 형식 (강제):
          ## 현재 데이터 타입
          - Item(name: str, price: float, quantity: int)
          - Order(order_id: int, items: List[Item], ...)

          ## 변경 금지 시그니처
          - add_order(self, order_id: int, items: List[Item]) -> None
          - cancel_order(self, order_id: int) -> None

          ## 이번에 추가할 것
          - get_order_history() 메서드만 추가
        """
        prompt = f"""현재 코드를 분석하여 아래 형식으로 **짧게** 요약하세요.
각 섹션은 불렛 포인트 3개 이하로 제한하세요.

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

---
아래 형식으로 요약을 작성하세요 (다른 설명 없이 이 형식만 출력):

## 현재 데이터 타입
(코드에서 실제로 사용되는 클래스와 필드를 타입과 함께, 최대 5개)

## 변경 금지 시그니처
(이번 수정에서 절대 바꾸면 안 되는 기존 메서드 시그니처, 최대 5개)

## 이번에 추가할 것
(수정 요청에서 새로 추가해야 하는 것만, 최대 3개)"""

        return self.call_llm(
            prompt,
            "당신은 코드 요약 전문가입니다. 간결하고 정확하게 요약하세요. 불필요한 설명은 생략하세요.")

    # ─── 코드 생성 (Summary를 맨 앞에 배치) ────────────────────────────────────

    def _generate_modified_code(self, current_code: str,
                                modification_request: str,
                                summary: str) -> str:
        """
        Summary를 프롬프트 맨 앞에 배치하여 코드를 생성한다.

        새 프롬프트 구조 (Lost in the Middle 해결):
          [Summary — 짧고 구체적]  ← 시작, LLM이 가장 집중
          [현재 코드]
          [수정 요청]               ← 끝, LLM이 두 번째로 집중

        Spec/Plan/Constraints 같은 긴 문서는 제거.
        중간에 끼는 내용을 최소화하여 핵심 정보가 무시되지 않도록 한다.
        """
        system_prompt = """당신은 Python 개발자입니다.
반드시 프롬프트 맨 앞의 '구현 요약'에 명시된 타입과 시그니처를 그대로 유지하세요.
절대 기존 데이터 타입을 바꾸지 마세요."""

        prompt = f"""## 구현 요약 ← 반드시 준수하세요
{summary}

---

## 현재 코드
```python
{current_code}
```

## 수정 요청
{modification_request}

**위 구현 요약의 '변경 금지 시그니처'와 '현재 데이터 타입'을 그대로 유지하면서**
'이번에 추가할 것'만 구현하세요. 완전한 수정된 코드를 작성하세요."""

        return self.extract_code(self.call_llm(prompt, system_prompt))
