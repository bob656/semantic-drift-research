from dataclasses import dataclass
from typing import Dict, List, Optional

# 핵심 수치 상수
INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015

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
    payments: List[Payment] = dataclass.field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: Dict[int, Loan] = {}
        self.payment_counter: int = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, 'active')
        return True

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return []
        return loan.payments

    def calculate_monthly_payment(self, loan_id: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

# Example usage:
loan_system = LoanSystem()
if loan_system.create_loan(1, "John Doe", 1000000, 36):
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid term.")

monthly_payment = loan_system.calculate_monthly_payment(1)
if monthly_payment is not None:
    print(f"Monthly payment: {monthly_payment:.2f}원")
else:
    print("Failed to calculate monthly payment.")

loan_system.record_payment(1, 50000, '2023-10-01')
payment_history = loan_system.get_payment_history(1)
for payment in payment_history:
    print(f"Payment - ID: {payment.payment_id}, Amount: {payment.amount:.2f}원, Date: {payment.date}, Type: {payment.type}")

loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
if loan:
    print(f"Loan details - ID: {loan.loan_id}, Borrower: {loan.borrower}, Principal: {loan.principal:.2f}원, Months: {loan.months}, Status: {loan.status}")
else:
    print("Loan not found.")