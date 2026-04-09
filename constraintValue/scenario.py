"""
scenario.py — 수치 계약 보존 실험 시나리오

## 연구 배경

Science China Information Sciences (2025) 및 NeurIPS 2023 연구에 따르면
LLM은 코드 생성 시 수치 상수(Constant Value Error)를 자주 잘못 다룬다.

이 시나리오는 반복 수정 과정에서 수치 계약이 얼마나 보존되는지 측정한다.

## 핵심 수치 계약 (LoanSystem)

  INTEREST_RATE     = 0.025   (연이율 2.5%)
  LATE_FEE          = 5000    (연체료 5,000원)
  MAX_INSTALLMENTS  = 36      (최대 할부 36개월)
  MIN_PAYMENT       = 10_000  (최소 납입액 10,000원)
  PENALTY_RATE      = 0.015   (연체 가산율 1.5%)

## 수정 시나리오 (5단계)

  수정1: 납부 이력 관리 기능 추가
  수정2: 조기 상환 할인 계산 추가
  수정3: 연체 알림 조건 추가
  수정4: 분할 납부 계획 생성 기능 추가
  수정5: 월별 리포트 출력 기능 추가

  → 모든 수정이 위의 수치 상수를 변경할 이유가 없지만
    LLM이 임의로 바꾸는 경향이 있음 (Constant Value Error)
"""

SCENARIO = {
    'name': 'LoanSystem — Numeric Constraint Preservation',

    'initial_task': """다음 요구사항을 만족하는 LoanSystem 클래스를 Python으로 구현하세요.

[핵심 수치 상수 — 절대 변경 금지]
- 연이율(INTEREST_RATE): 0.025 (2.5%)
- 연체료(LATE_FEE): 5000원
- 최대 할부 개월 수(MAX_INSTALLMENTS): 36개월
- 최소 납입액(MIN_PAYMENT): 10000원
- 연체 가산율(PENALTY_RATE): 0.015 (1.5%)

[구현할 기능]
1. Loan 데이터 클래스: loan_id(int), borrower(str), principal(float), months(int), status(str)
2. LoanSystem 클래스:
   - create_loan(loan_id, borrower, principal, months): 대출 생성, months > MAX_INSTALLMENTS면 거부
   - calculate_monthly_payment(loan_id): 원리금 균등상환 공식으로 월 납입액 계산
     * 공식: principal * r / (1 - (1+r)^(-months)), r = INTEREST_RATE/12
     * 계산 결과가 MIN_PAYMENT 미만이면 MIN_PAYMENT 반환
   - apply_late_fee(loan_id): 연체 시 LATE_FEE + 잔액 * PENALTY_RATE 추가
   - get_loan(loan_id): 대출 조회
""",

    'modifications': [
        # 수정1: 납부 이력 — 수치 변경 이유 없음
        """납부 이력 관리 기능을 추가하세요.

Payment 데이터 클래스 추가: payment_id(int), loan_id(int), amount(float), date(str), type(str)

LoanSystem에 메서드 추가:
- record_payment(loan_id, amount, date, payment_type='REGULAR'): 납부 기록 저장
- get_payment_history(loan_id): 해당 대출의 납부 이력 반환

기존 수치 상수(INTEREST_RATE=0.025, LATE_FEE=5000, MAX_INSTALLMENTS=36,
MIN_PAYMENT=10000, PENALTY_RATE=0.015)는 그대로 유지하세요.""",

        # 수정2: 조기 상환 할인 — 수치 변경 이유 없음
        """조기 상환 할인 계산 기능을 추가하세요.

LoanSystem에 메서드 추가:
- calculate_early_repayment(loan_id, remaining_balance): 조기 상환 시 절감 이자 계산
  * 잔여 이자 = remaining_balance * INTEREST_RATE / 12 * remaining_months
  * 조기 상환 할인액 = 잔여 이자 * 0.1 (10% 할인, 이 비율만 새로 추가)
- get_payoff_amount(loan_id): 현재 시점 완납 금액 반환

기존 수치 상수(INTEREST_RATE=0.025, LATE_FEE=5000, MAX_INSTALLMENTS=36,
MIN_PAYMENT=10000, PENALTY_RATE=0.015)는 절대 변경하지 마세요.""",

        # 수정3: 연체 알림 — 수치 변경 이유 없음
        """연체 감지 및 알림 조건 기능을 추가하세요.

LoanSystem에 메서드 추가:
- check_overdue(loan_id, last_payment_date, today): 연체 여부 확인
  * 30일 이상 납부 없으면 연체로 판정 (30은 새로 추가하는 수치)
- get_overdue_amount(loan_id): 연체 총액 반환
  * 연체 총액 = 미납 원금 + LATE_FEE + 미납 원금 * PENALTY_RATE

기존 수치 상수(INTEREST_RATE=0.025, LATE_FEE=5000, MAX_INSTALLMENTS=36,
MIN_PAYMENT=10000, PENALTY_RATE=0.015)는 절대 변경하지 마세요.""",

        # 수정4: 분할 납부 계획 — 수치 변경 이유 없음
        """분할 납부 계획 생성 기능을 추가하세요.

LoanSystem에 메서드 추가:
- generate_payment_schedule(loan_id): 전체 납부 계획표 생성
  * 각 회차별: 회차번호, 납입액, 원금 부분, 이자 부분, 잔액
  * 이자 계산: 잔액 * INTEREST_RATE / 12
- get_remaining_balance(loan_id, paid_months): 납부 완료 월 수 기준 잔액 계산

기존 수치 상수(INTEREST_RATE=0.025, LATE_FEE=5000, MAX_INSTALLMENTS=36,
MIN_PAYMENT=10000, PENALTY_RATE=0.015)는 절대 변경하지 마세요.""",

        # 수정5: 월별 리포트 — 수치 변경 이유 없음
        """월별 대출 현황 리포트 기능을 추가하세요.

LoanSystem에 메서드 추가:
- generate_monthly_report(year, month): 해당 월 대출 현황 딕셔너리 반환
  * total_loans: 전체 대출 건수
  * total_principal: 전체 원금 합계
  * average_rate: 평균 이율 (INTEREST_RATE 기반)
  * overdue_count: 연체 건수
  * total_late_fees: 연체료 합계 (건당 LATE_FEE 기준)
- summarize_portfolio(): 전체 포트폴리오 요약 반환

기존 수치 상수(INTEREST_RATE=0.025, LATE_FEE=5000, MAX_INSTALLMENTS=36,
MIN_PAYMENT=10000, PENALTY_RATE=0.015)는 절대 변경하지 마세요.""",
    ],

    # 보존되어야 할 수치 계약 목록 (evaluator에서 사용)
    'numeric_contracts': {
        'INTEREST_RATE':    0.025,
        'LATE_FEE':         5000,
        'MAX_INSTALLMENTS': 36,
        'MIN_PAYMENT':      10000,
        'PENALTY_RATE':     0.015,
    },
}
