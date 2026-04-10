from typing import List, Optional
from datetime import datetime

INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015

class Payment:
    def __init__(self, payment_id: int, loan_id: int, amount: float, date: str, type: str):
        self.payment_id = payment_id
        self.loan_id = loan_id
        self.amount = amount
        self.date = date
        self.type = type

class Loan:
    def __init__(self, loan_id: int, borrower: str, principal: float, months: int, status: str):
        self.loan_id = loan_id
        self.borrower = borrower
        self.principal = principal
        self.months = months
        self.status = status
        self.payment_history: List[Payment] = []

class LoanSystem:
    def __init__(self):
        self.loans: List[Loan] = []
        self.next_payment_id = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans.append(new_loan)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> Optional[float]:
        for loan in self.loans:
            if loan.loan_id == loan_id and loan.status == "active":
                r = INTEREST_RATE / 12
                monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
                return max(monthly_payment, MIN_PAYMENT)
        return None

    def apply_late_fee(self, loan_id: int):
        for loan in self.loans:
            if loan.loan_id == loan_id and loan.status == "active":
                late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
                loan.principal += late_fee
                break

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        for loan in self.loans:
            if loan.loan_id == loan_id:
                return loan
        return None

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        for loan in self.loans:
            if loan.loan_id == loan_id and loan.status == "active":
                new_payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
                loan.payment_history.append(new_payment)
                self.next_payment_id += 1
                break

    def get_payment_history(self, loan_id: int) -> Optional[List[Payment]]:
        for loan in self.loans:
            if loan.loan_id == loan_id:
                return loan.payment_history
        return None

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        r = INTEREST_RATE / 12
        remaining_months = loan.months - len(loan.payment_history)
        residual_interest = remaining_balance * r * remaining_months
        early_repayment_discount = residual_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        remaining_balance = loan.principal
        for payment in loan.payment_history:
            remaining_balance -= payment.amount
        
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        last_payment_datetime = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        days_overdue = (today_datetime - last_payment_datetime).days
        return days_overdue > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        overdue_principal = 0
        for payment in loan.payment_history:
            if (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(payment.date, "%Y-%m-%d")).days > 30:
                overdue_principal += payment.amount
        
        overdue_interest = overdue_principal * INTEREST_RATE
        overdue_penalty = overdue_principal * PENALTY_RATE
        return overdue_principal + overdue_interest + overdue_penalty

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 100000, 36)
print(loan_system.calculate_monthly_payment(1))  # Should print the calculated monthly payment or MIN_PAYMENT if lower
loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
if loan:
    print(f"Loan ID: {loan.loan_id}, Borrower: {loan.borrower}, Principal: {loan.principal}, Months: {loan.months}, Status: {loan.status}")
loan_system.record_payment(loan_id=1, amount=20000, date="2023-10-01")
payment_history = loan_system.get_payment_history(loan_id=1)
if payment_history:
    for payment in payment_history:
        print(f"Payment ID: {payment.payment_id}, Loan ID: {payment.loan_id}, Amount: {payment.amount}, Date: {payment.date}, Type: {payment.type}")

# New functionality usage
early_repayment_discount = loan_system.calculate_early_repayment(1, 80000)
print(f"Early Repayment Discount: {early_repayment_discount}")
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff Amount: {payoff_amount}")

# Overdue functionality usage
is_overdue = loan_system.check_overdue(loan_id=1, last_payment_date="2023-09-01", today="2023-10-15")
print(f"Is the loan overdue? {is_overdue}")
overdue_amount = loan_system.get_overdue_amount(loan_id=1)
print(f"Overdue Amount: {overdue_amount}")