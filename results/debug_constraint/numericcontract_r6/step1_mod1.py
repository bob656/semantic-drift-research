from dataclasses import dataclass, field
from typing import Dict, Optional, List

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

@dataclass
class Loan:
    loan_id: int
    borrower: str
    principal: float
    months: int
    status: str = field(default="active")

@dataclass
class Payment:
    payment_id: int
    loan_id: int
    amount: float
    date: str
    type: str

class LoanSystem:
    def __init__(self):
        self.loans: Dict[int, Loan] = {}
        self.payments: List[Payment] = []

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months)
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        # Assuming each payment is unique and we generate a simple ID for demonstration
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id=payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        self.payments.append(payment)

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        return [payment for payment in self.payments if payment.loan_id == loan_id]

# Example usage:
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 500000.0, 36)
monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly Payment: {monthly_payment}")
loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
print(f"Loan after late fee: {loan.principal}")

# Recording payments
loan_system.record_payment(1, 50000.0, "2023-10-01")
loan_system.record_payment(1, 50000.0, "2023-11-01", payment_type='PREPAYMENT')

# Getting payment history
payment_history = loan_system.get_payment_history(1)
for payment in payment_history:
    print(f"Payment ID: {payment.payment_id}, Amount: {payment.amount}, Date: {payment.date}, Type: {payment.type}")