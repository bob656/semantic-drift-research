from dataclasses import dataclass
from typing import Dict, Optional

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
        self.loans: Dict[int, Loan] = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, 'active')
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        late_fee_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee_amount

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

# Example usage:
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 500000, 36)
if loan_created:
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid term.")

monthly_payment = loan_system.calculate_monthly_payment(1)
if monthly_payment is not None:
    print(f"Monthly payment: {monthly_payment}원")
else:
    print("Failed to calculate monthly payment or loan does not exist.")

loan_system.apply_late_fee(1)

loan = loan_system.get_loan(1)
if loan:
    print(f"Loan details: ID={loan.loan_id}, Borrower={loan.borrower}, Principal={loan.principal}원, Months={loan.months}")
else:
    print("Loan not found.")