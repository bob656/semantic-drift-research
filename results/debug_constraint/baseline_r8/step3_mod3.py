from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 핵심 수치 상수
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5,000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10,000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

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
    payments: list[Payment] = field(default_factory=list)

    def remaining_months(self) -> int:
        """대출의 잔여 월 수를 계산합니다."""
        return max(0, self.months - len(self.payments))

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_id_counter = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False  # 최대 할부 개월 수를 초과하면 거부
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, "active")
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12  # 월 이율
        monthly_payment = (loan.principal * r) / (1 - (1 + r)**(-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        penalty_amount = LATE_FEE + loan.principal * PENALTY_RATE
        loan.principal += penalty_amount
        loan.status = "late"

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        payment = Payment(payment_id=self.payment_id_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_id_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        return loan.payments

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        return self.loans[loan_id]

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        """조기 상환 시 절감 이자 계산"""
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12  # 월 이율
        remaining_months = loan.remaining_months()
        remaining_interest = remaining_balance * r * remaining_months
        discount_amount = remaining_interest * 0.1  # 10% 할인
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        """현재 시점 완납 금액 반환"""
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        remaining_balance = loan.principal
        for payment in loan.payments:
            remaining_balance -= payment.amount
        return max(0, remaining_balance)

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        return (current_date - last_payment).days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        overdue_interest = loan.principal * INTEREST_RATE
        late_fee = LATE_FEE
        penalty_amount = loan.principal * PENALTY_RATE
        
        return loan.principal + overdue_interest + late_fee + penalty_amount

# 예시 사용
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 500000, 24)
monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"월 납입액: {monthly_payment:.2f}원")
loan_system.record_payment(1, monthly_payment, "2023-10-01")
payment_history = loan_system.get_payment_history(1)
for payment in payment_history:
    print(f"납부 이력: {payment}")
loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
print(f"대출 정보: {loan}")

# 연체 감지 및 알림 예시
overdue_status = loan_system.check_overdue(1, "2023-09-01", "2023-10-15")
if overdue_status:
    print("대출이 연체되었습니다.")
else:
    print("대출이 정상입니다.")

# 연체 총액 반환 예시
overdue_amount = loan_system.get_overdue_amount(1)
print(f"연체 총액: {overdue_amount:.2f}원")

# 조기 상환 시 절감 이자 계산 예시
early_repayment_discount = loan_system.calculate_early_repayment(1, 500000 - monthly_payment)
print(f"조기 상환 할인액: {early_repayment_discount:.2f}원")

# 현재 시점 완납 금액 반환 예시
payoff_amount = loan_system.get_payoff_amount(1)
print(f"현재 시점 완납 금액: {payoff_amount:.2f}원")