from dataclasses import dataclass
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
    status: str
    payments: list[Payment] = None  # Initialize as empty list

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # To generate unique payment IDs

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, "active", [])
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return
        loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    # New methods for payment history management
    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return False
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1
        return True

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return []
        return loan.payments

    # New methods for early repayment calculation
    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        return remaining_balance

    # New methods for overdue detection and notification
    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return False
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        overdue_days = (current_date - last_payment).days
        return overdue_days >= 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        overdue_interest = remaining_balance * (INTEREST_RATE / 12) * 30  # Assuming 30 days overdue for simplicity
        late_fee = LATE_FEE
        penalty_interest = remaining_balance * PENALTY_RATE
        return remaining_balance + overdue_interest + late_fee + penalty_interest

    # New methods for payment schedule and remaining balance
    def generate_payment_schedule(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return []
        
        r = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        remaining_principal = loan.principal
        schedule = []

        for month in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = monthly_payment - interest_payment
            if principal_payment < 0:
                principal_payment = 0
            remaining_principal -= principal_payment

            schedule.append({
                "installment_number": month,
                "payment_amount": monthly_payment,
                "principal_payment": principal_payment,
                "interest_payment": interest_payment,
                "remaining_balance": remaining_principal
            })

        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        
        r = INTEREST_RATE / 12
        monthly_payment = max(self.calculate_monthly_payment(loan_id), MIN_PAYMENT)
        remaining_principal = loan.principal

        for month in range(1, min(paid_months + 1, loan.months + 1)):
            interest_payment = remaining_principal * r
            principal_payment = monthly_payment - interest_payment
            if principal_payment < 0:
                principal_payment = 0
            remaining_principal -= principal_payment

        return remaining_principal

    # New methods for monthly report generation
    def generate_monthly_report(self, year: int, month: int):
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }

        for loan in self.loans.values():
            if loan.status != "active":
                continue

            report["total_loans"] += 1
            report["total_principal"] += loan.principal

            # Check if the loan is overdue
            if self.check_overdue(loan.loan_id, loan.payments[-1].date if loan.payments else "", f"{year}-{month:02d}-01"):
                report["overdue_count"] += 1
                report["total_late_fees"] += LATE_FEE

        # Calculate average interest rate (assuming all loans have the same rate)
        report["average_rate"] = INTEREST_RATE if report["total_loans"] > 0 else 0.0

        return report

    def summarize_portfolio(self):
        summary = {
            "active_loans": len([loan for loan in self.loans.values() if loan.status == "active"]),
            "inactive_loans": len([loan for loan in self.loans.values() if loan.status != "active"]),
            "total_principal": sum(loan.principal for loan in self.loans.values()),
            "average_monthly_payment": sum(self.calculate_monthly_payment(loan.loan_id) for loan in self.loans.values()) / len(self.loans),
        }
        return summary

# 테스트 코드
loan_system = LoanSystem()
loan_system.create_loan(1, "Alice", 1000000, 24)
print("Monthly Payment:", loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print("Loan after late fee:", loan_system.get_loan(1).principal)

# Test payment history
loan_system.record_payment(1, 50000, "2023-10-01")
loan_system.record_payment(1, 60000, "2023-11-01", payment_type='EARLY')
print("Payment History:", [payment.amount for payment in loan_system.get_payment_history(1)])

# Test early repayment discount
remaining_balance = loan_system.get_payoff_amount(1)
discount = loan_system.calculate_early_repayment_discount(remaining_balance, 22)  # Assuming 22 months remaining
print(f"Early Repayment Discount: {discount}")

# Test overdue detection and notification
overdue_status = loan_system.check_overdue(1, "2023-09-01", "2023-10-15")
print("Overdue Status:", overdue_status)
overdue_amount = loan_system.get_overdue_amount(1)
print("Overdue Amount:", overdue_amount)

# Test payment schedule
payment_schedule = loan_system.generate_payment_schedule(1)
for entry in payment_schedule[:5]:  # Print first 5 installments
    print(entry)

# Test remaining balance after some payments
remaining_balance_after_2_months = loan_system.get_remaining_balance(1, 2)
print("Remaining Balance After 2 Months:", remaining_balance_after_2_months)

# Test monthly report generation
monthly_report = loan_system.generate_monthly_report(2023, 10)
print("Monthly Report:", monthly_report)

# Test portfolio summary
portfolio_summary = loan_system.summarize_portfolio()
print("Portfolio Summary:", portfolio_summary)