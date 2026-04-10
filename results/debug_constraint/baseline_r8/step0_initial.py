from dataclasses import dataclass

# 핵심 수치 상수
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5,000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10,000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

@dataclass
class Loan:
    loan_id: int
    borrower: str
    principal: float
    months: int
    status: str

class LoanSystem:
    def __init__(self):
        self.loans = {}

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

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        return self.loans[loan_id]

# 예시 사용
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 500000, 24)
monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"월 납입액: {monthly_payment:.2f}원")
loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
print(f"대출 정보: {loan}")