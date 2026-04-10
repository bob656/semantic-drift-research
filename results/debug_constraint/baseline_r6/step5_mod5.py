from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 핵심 수치 상수 — 절대 변경 금지
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
    status: str = field(default="active")
    payments: list[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.next_payment_id: int = 1

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
        
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.next_payment_id += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        return loan.payments

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        remaining_months = len([p for p in loan.payments if p.type == 'REGULAR']) - len([p for p in loan.payments if p.amount > self.calculate_monthly_payment(loan_id)])
        residual_interest = remaining_balance * r * remaining_months
        early_repayment_discount = residual_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(p.amount for p in loan.payments if p.type == 'REGULAR')
        return max(total_paid + (loan.principal - total_paid), MIN_PAYMENT)

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        last_payment_datetime = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        delta = today_datetime - last_payment_datetime
        return delta.days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        overdue_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        overdue_interest_rate = INTEREST_RATE * 1.5
        overdue_days = sum((datetime.strptime(p.date, "%Y-%m-%d") - datetime.strptime(loan.payments[i-1].date, "%Y-%m-%d")).days for i, p in enumerate(loan.payments) if i > 0 and (datetime.strptime(p.date, "%Y-%m-%d") - datetime.strptime(loan.payments[i-1].date, "%Y-%m-%d")).days > 30)
        overdue_interest = loan.principal * overdue_interest_rate * (overdue_days / 365)
        
        return loan.principal + overdue_fee + overdue_interest

    def generate_payment_schedule(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        schedule = []
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        monthly_payment = self.calculate_monthly_payment(loan_id)
        
        for month in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = monthly_payment - interest_payment
            if remaining_principal <= principal_payment:
                principal_payment = remaining_principal
                interest_payment = 0
            
            schedule.append({
                "installment_number": month,
                "payment_amount": round(monthly_payment, 2),
                "principal_payment": round(principal_payment, 2),
                "interest_payment": round(interest_payment, 2),
                "remaining_balance": round(remaining_principal - principal_payment, 2)
            })
            
            remaining_principal -= principal_payment
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        
        for _ in range(paid_months):
            interest_payment = remaining_principal * r
            principal_payment = self.calculate_monthly_payment(loan_id) - interest_payment
            if remaining_principal <= principal_payment:
                principal_payment = remaining_principal
                interest_payment = 0
            
            remaining_principal -= principal_payment
        
        return round(remaining_principal, 2)

    def generate_monthly_report(self, year: int, month: int):
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }
        
        for loan in self.loans.values():
            if self._is_loan_in_month(loan, year, month):
                report["total_loans"] += 1
                report["total_principal"] += loan.principal
                
                # Average rate calculation (assuming a fixed interest rate)
                report["average_rate"] += INTEREST_RATE
                
                if self._is_overdue(loan, year, month):
                    report["overdue_count"] += 1
                    report["total_late_fees"] += LATE_FEE + (loan.principal * PENALTY_RATE)
        
        if report["total_loans"] > 0:
            report["average_rate"] /= report["total_loans"]
        
        return report

    def summarize_portfolio(self):
        summary = {
            "total_active_loans": 0,
            "total_principal_outstanding": 0.0,
            "average_interest_rate": INTEREST_RATE,  # Assuming a fixed interest rate
            "overdue_loans_count": 0,
            "total_late_fees_collected": 0.0
        }
        
        for loan in self.loans.values():
            if loan.status == "active":
                summary["total_active_loans"] += 1
                summary["total_principal_outstanding"] += loan.principal
                
                if self._is_overdue(loan, datetime.now().year, datetime.now().month):
                    summary["overdue_loans_count"] += 1
                    summary["total_late_fees_collected"] += LATE_FEE + (loan.principal * PENALTY_RATE)
        
        return summary

    def _is_loan_in_month(self, loan: Loan, year: int, month: int) -> bool:
        # Assuming the first payment date is used to determine if a loan is in a given month
        first_payment_date = datetime.strptime(loan.payments[0].date, "%Y-%m-%d") if loan.payments else None
        return first_payment_date and first_payment_date.year == year and first_payment_date.month == month

    def _is_overdue(self, loan: Loan, year: int, month: int) -> bool:
        # Check if the latest payment date is before the end of the given month
        latest_payment_date = max(datetime.strptime(p.date, "%Y-%m-%d") for p in loan.payments) if loan.payments else None
        last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return latest_payment_date and latest_payment_date < last_day_of_month

# Example usage:
loan_system = LoanSystem()
# Assuming some loans are added to the system with payments recorded...

monthly_report = loan_system.generate_monthly_report(2023, 10)
portfolio_summary = loan_system.summarize_portfolio()

print("Monthly Report:", monthly_report)
print("Portfolio Summary:", portfolio_summary)