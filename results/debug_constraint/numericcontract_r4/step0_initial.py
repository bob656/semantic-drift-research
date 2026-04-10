from dataclasses import dataclass

# 핵심 수치 상수
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
    status: str = "active"

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        penalty = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty

    def get_loan(self, loan_id: int) -> Loan:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        return loan