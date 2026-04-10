from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime, timedelta

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

    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount_amount = remaining_interest * 0.1
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        # Calculate the remaining balance by subtracting payments
        total_paid = sum(payment.amount for payment in self.payments if payment.loan_id == loan_id)
        remaining_balance = loan.principal - total_paid
        
        # Calculate monthly interest rate
        r = INTEREST_RATE / 12
        
        # Calculate the remaining number of months
        remaining_months = loan.months
        
        # Calculate the remaining balance considering interest
        for _ in range(remaining_months):
            interest = remaining_balance * r
            remaining_balance += interest
        
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        last_payment_datetime = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        difference = today_datetime - last_payment_datetime
        return difference.days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        # Calculate the remaining balance by subtracting payments
        total_paid = sum(payment.amount for payment in self.payments if payment.loan_id == loan_id)
        remaining_balance = loan.principal - total_paid
        
        # Calculate overdue amount (remaining balance + late fee + penalty interest)
        overdue_amount = remaining_balance + LATE_FEE + (remaining_balance * PENALTY_RATE)
        
        return overdue_amount

    def generate_payment_schedule(self, loan_id: int) -> List[Dict[str, float]]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        r = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        schedule = []
        remaining_balance = loan.principal
        
        for month in range(1, loan.months + 1):
            interest = remaining_balance * r
            principal_payment = monthly_payment - interest
            remaining_balance -= principal_payment
            
            schedule.append({
                "month": month,
                "payment_amount": monthly_payment,
                "principal": principal_payment,
                "interest": interest,
                "balance": remaining_balance
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan not found or already paid off.")
        
        r = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        remaining_balance = loan.principal
        
        for _ in range(paid_months):
            interest = remaining_balance * r
            principal_payment = monthly_payment - interest
            remaining_balance -= principal_payment
        
        return remaining_balance

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

# Calculate early repayment discount and payoff amount
remaining_balance = 300000.0  # Example remaining balance after payments
remaining_months = 24  # Example remaining months
discount = loan_system.calculate_early_repayment_discount(remaining_balance, remaining_months)
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Early Repayment Discount: {discount}")
print(f"Payoff Amount: {payoff_amount}")

# Check overdue and get overdue amount
is_overdue = loan_system.check_overdue(1, "2023-09-01", "2023-10-15")
overdue_amount = loan_system.get_overdue_amount(1)
print(f"Is Overdue: {is_overdue}")
print(f"Overdue Amount: {overdue_amount}")

# Generate payment schedule and get remaining balance
payment_schedule = loan_system.generate_payment_schedule(1)
for entry in payment_schedule:
    print(entry)

remaining_balance_after_2_months = loan_system.get_remaining_balance(1, 2)
print(f"Remaining Balance after 2 months: {remaining_balance_after_2_months}")