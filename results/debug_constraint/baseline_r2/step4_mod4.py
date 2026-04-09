from dataclasses import dataclass
from datetime import datetime

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000        # 연체료 (5000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000    # 최소 납입액 (10000원)
PENALTY_RATE = 0.015   # 연체 가산율 (1.5%)

@dataclass
class Payment:
    payment_id: int
    loan_id: int
    amount: float
    date: str
    type: str

@dataclass
class Loan:
    loan_id: int
    borrower: str
    principal: float
    months: int
    status: str
    payments: list[Payment] = None  # Initialize with an empty list of payments

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # Unique identifier for each payment

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, 'active', [])
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan:
            return []
        return loan.payments

    # 추가된 메서드
    def generate_payment_schedule(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return []

        schedule = []
        remaining_balance = loan.principal
        for month in range(1, loan.months + 1):
            interest = remaining_balance * INTEREST_RATE / 12
            principal_payment = self.calculate_monthly_payment(loan_id) - interest
            total_payment = interest + principal_payment

            schedule.append({
                'month': month,
                'total_payment': round(total_payment, 2),
                'principal_payment': round(principal_payment, 2),
                'interest_payment': round(interest, 2),
                'remaining_balance': round(remaining_balance - principal_payment, 2)
            })

            remaining_balance -= principal_payment

        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0

        remaining_balance = loan.principal
        for _ in range(paid_months):
            interest = remaining_balance * INTEREST_RATE / 12
            principal_payment = self.calculate_monthly_payment(loan_id) - interest
            remaining_balance -= principal_payment

        return round(remaining_balance, 2)

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        r = INTEREST_RATE / 12
        remaining_months = loan.months - len(loan.payments)
        interest_to_save = remaining_balance * r * remaining_months
        discount_amount = interest_to_save * 0.1  # 10% 할인
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        remaining_balance = loan.principal - sum(payment.amount for payment in loan.payments)
        return remaining_balance

    # 연체 여부 확인 메서드 추가
    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return False
        
        # 날짜 형식 변환
        last_payment_date = datetime.strptime(last_payment_date, '%Y-%m-%d')
        today = datetime.strptime(today, '%Y-%m-%d')

        # 30일 이상 지나면 연체로 판정
        if (today - last_payment_date).days > 30:
            return True
        else:
            return False

    # 연체 총액 반환 메서드 추가
    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        
        remaining_balance = loan.principal - sum(payment.amount for payment in loan.payments)

        # 연체 총액 계산
        overdue_amount = remaining_balance + LATE_FEE + (remaining_balance * PENALTY_RATE)
        return overdue_amount

# Example usage:
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 36)
print(loan_system.calculate_monthly_payment(1))  # Calculate monthly payment
loan_system.apply_late_fee(1)                  # Apply late fee
loan_system.record_payment(1, 50000, '2023-04-01')  # Record a payment

# 연체 여부 확인
print(loan_system.check_overdue(1, '2023-03-01', '2023-04-15'))  # True (연체)

# 연체 총액 반환
print(loan_system.get_overdue_amount(1))         # 연체 총액 출력

print(loan_system.get_loan(1))                 # Get loan details
print(loan_system.get_payment_history(1))        # Get payment history
print(loan_system.calculate_early_repayment(1, 950000))  # Calculate early repayment discount
print(loan_system.get_payoff_amount(1))         # Get payoff amount

# 분할 납부 계획 생성 및 잔액 확인
schedule = loan_system.generate_payment_schedule(1)
for item in schedule[:5]:  # 첫 5개 회차만 출력
    print(item)

remaining_balance = loan_system.get_remaining_balance(1, 6)  # 6개월 후 잔액
print(f"Remaining balance after 6 months: {remaining_balance}")