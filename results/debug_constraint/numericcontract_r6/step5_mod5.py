from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

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

    def generate_monthly_report(self, year: int, month: int) -> Dict[str, float]:
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }
        
        for loan in self.loans.values():
            if not loan.status == "active":
                continue
            
            report["total_loans"] += 1
            report["total_principal"] += loan.principal

            # Overdue check
            last_payment = max(self.get_payment_history(loan.loan_id), key=lambda x: datetime.strptime(x.date, "%Y-%m-%d"), default=None)
            if last_payment:
                is_overdue = self.check_overdue(loan.loan_id, last_payment.date, f"{year}-{month}-01")
                if is_overdue:
                    report["overdue_count"] += 1
                    report["total_late_fees"] += LATE_FEE

        if report["total_loans"] > 0:
            report["average_rate"] = INTEREST_RATE
        
        return report

    def summarize_portfolio(self) -> Dict[str, float]:
        summary = {
            "total_active_loans": 0,
            "total_principal_outstanding": 0.0,
            "average_interest_rate": INTEREST_RATE,
            "total_overdue_count": 0,
            "total_late_fees_collected": 0.0
        }
        
        for loan in self.loans.values():
            if not loan.status == "active":
                continue
            
            summary["total_active_loans"] += 1
            summary["total_principal_outstanding"] += loan.principal

            # Overdue check and late fees calculation
            last_payment = max(self.get_payment_history(loan.loan_id), key=lambda x: datetime.strptime(x.date, "%Y-%m-%d"), default=None)
            if last_payment:
                is_overdue = self.check_overdue(loan.loan_id, last_payment.date, f"{datetime.now().year}-{datetime.now().month}-01")
                if is_overdue:
                    summary["total_overdue_count"] += 1
                    summary["total_late_fees_collected"] += LATE_FEE

        return summary