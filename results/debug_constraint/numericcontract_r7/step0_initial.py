from dataclasses import dataclass

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015

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
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, "active")
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return
        loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

# 테스트 코드
loan_system = LoanSystem()
loan_system.create_loan(1, "Alice", 1000000, 24)
print("Monthly Payment:", loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print("Loan after late fee:", loan_system.get_loan(1).principal)