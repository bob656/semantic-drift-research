from dataclasses import dataclass
from typing import Optional, List

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

@dataclass
class Payment:
    payment_id: int
    loan_id: int
    amount: float
    date: str
    type: str

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}  # Dictionary to store payment history for each loan
        self.next_payment_id = 1  # Counter for unique payment IDs

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, 'active')
        self.payment_history[loan_id] = []  # Initialize payment history for the new loan
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
        loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)
    
    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Invalid loan ID or inactive loan")
        payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        self.payment_history[loan_id].append(payment)
        self.next_payment_id += 1
        # For simplicity, we assume the payment is applied immediately to the principal
        loan.principal -= amount

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        return self.payment_history.get(loan_id, [])

    def calculate_early_repayment(self, loan_id: int, remaining_balance):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        remaining_months = loan.months - len(self.payment_history[loan_id])
        if remaining_months <= 0:
            return 0

        interest_to_pay = remaining_balance * INTEREST_RATE * remaining_months
        discount = interest_to_pay * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None

        monthly_payment = self.calculate_monthly_payment(loan_id)
        remaining_payments = len(self.payment_history[loan_id])
        remaining_balance = loan.principal + (remaining_payments * monthly_payment)

        interest_to_pay = remaining_balance * INTEREST_RATE * remaining_payments
        payoff_amount = remaining_balance + interest_to_pay

        return payoff_amount

# Example usage:
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
print(loan_system.calculate_monthly_payment(1))  # Should print the calculated monthly payment
loan_system.record_payment(1, 50000, '2023-01-01')
print(loan_system.get_loan(1).principal)  # Should print the updated principal after the payment
print([payment.amount for payment in loan_system.get_payment_history(1)])  # Should print the payment history for loan ID 1

discount = loan_system.calculate_early_repayment(1, 50000)
print(f"Early repayment discount: {discount}")

payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff amount: {payoff_amount}")