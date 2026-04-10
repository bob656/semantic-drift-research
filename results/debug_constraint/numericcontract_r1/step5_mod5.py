from typing import List, Optional, Dict
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

    def generate_payment_schedule(self, loan_id: int):
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        principal = loan.principal
        monthly_interest_rate = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        
        payment_schedule = []
        for month in range(1, loan.months + 1):
            interest_payment = principal * monthly_interest_rate
            principal_payment = min(monthly_payment - interest_payment, principal)
            remaining_balance = principal - principal_payment
            
            payment_schedule.append({
                "Installment": month,
                "Payment Amount": monthly_payment,
                "Principal Payment": principal_payment,
                "Interest Payment": interest_payment,
                "Remaining Balance": remaining_balance
            })
            
            principal -= principal_payment
        
        return payment_schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        loan = self.get_loan(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Invalid loan ID or loan is not active.")
        
        if paid_months > loan.months:
            return 0
        
        principal = loan.principal
        monthly_interest_rate = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        
        for _ in range(paid_months):
            interest_payment = principal * monthly_interest_rate
            principal_payment = min(monthly_payment - interest_payment, principal)
            principal -= principal_payment
        
        return principal

    def generate_monthly_report(self, year: int, month: int) -> Dict[str, float]:
        total_loans = 0
        total_principal = 0
        total_late_fees = 0
        overdue_count = 0
        average_rate = 0.0

        for loan in self.loans:
            if loan.status == "active":
                total_loans += 1
                total_principal += loan.principal

                # Check if the loan is overdue
                last_payment_date = max(payment.date for payment in loan.payment_history) if loan.payment_history else None
                if last_payment_date and self.check_overdue(loan.loan_id, last_payment_date, f"{year}-{month:02d}-01"):
                    overdue_count += 1
                    total_late_fees += LATE_FEE + (loan.principal * PENALTY_RATE)

        average_rate = INTEREST_RATE if total_loans > 0 else 0.0

        return {
            "total_loans": total_loans,
            "total_principal": total_principal,
            "average_rate": average_rate,
            "overdue_count": overdue_count,
            "total_late_fees": total_late_fees
        }

    def summarize_portfolio(self) -> Dict[str, float]:
        total_active_loans = 0
        total_principal = 0
        total_interest_earned = 0

        for loan in self.loans:
            if loan.status == "active":
                total_active_loans += 1
                total_principal += loan.principal

                # Calculate interest earned so far (simplified)
                monthly_interest_rate = INTEREST_RATE / 12
                interest_earned = loan.principal * monthly_interest_rate * len(loan.payment_history)
                total_interest_earned += interest_earned

        return {
            "total_active_loans": total_active_loans,
            "total_principal": total_principal,
            "total_interest_earned": total_interest_earned
        }

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 100000, 36)
print(loan_system.calculate_monthly_payment(1))  # Should print the monthly payment amount

# Generate a monthly report for January 2024
monthly_report = loan_system.generate_monthly_report(2024, 1)
print(monthly_report)

# Summarize the portfolio
portfolio_summary = loan_system.summarize_portfolio()
print(portfolio_summary)