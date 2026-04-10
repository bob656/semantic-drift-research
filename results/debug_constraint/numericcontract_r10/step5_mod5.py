from dataclasses import dataclass, field
from datetime import datetime

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
    status: str = "active"
    payments: list = field(default_factory=list)

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
        self.payment_counter = 1  # Unique identifier for payments

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        late_fee_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee_amount

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        # Assuming a simple list to store payments for each loan
        self.loans[loan_id].payments.append(Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type))
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        return self.loans[loan_id].payments

    # 추가된 메서드
    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        remaining_principal = loan.principal
        monthly_interest_rate = INTEREST_RATE / 12
        monthly_payment = self.calculate_monthly_payment(loan_id)
        payment_schedule = []

        for month in range(1, loan.months + 1):
            interest_payment = remaining_principal * monthly_interest_rate
            principal_payment = max(monthly_payment - interest_payment, 0)
            remaining_balance = remaining_principal - principal_payment

            payment_schedule.append({
                'month': month,
                'payment_amount': round(monthly_payment),
                'principal_payment': round(principal_payment),
                'interest_payment': round(interest_payment),
                'remaining_balance': round(remaining_balance)
            })

            remaining_principal = remaining_balance

        return payment_schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_principal = loan.principal

        for _ in range(paid_months):
            interest_payment = remaining_principal * monthly_interest_rate
            principal_payment = max(self.calculate_monthly_payment(loan_id) - interest_payment, 0)
            remaining_principal -= principal_payment

        return round(remaining_principal)

    # 기존 메서드 유지
    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        # Assuming the last payment recorded is the most recent
        payments = loan.payments
        if not payments:
            return loan.principal
        last_payment = max(payments, key=lambda x: x.payment_id)
        remaining_balance = loan.principal - sum(payment.amount for payment in payments if payment.date <= last_payment.date)
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        return (current_date - last_payment).days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        overdue_principal = loan.principal
        overdue_interest = overdue_principal * INTEREST_RATE
        overdue_penalty = overdue_principal * PENALTY_RATE
        return overdue_principal + overdue_interest + overdue_penalty

    def generate_monthly_report(self, year: int, month: int):
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }

        for loan in self.loans.values():
            report["total_loans"] += 1
            report["total_principal"] += loan.principal

            # Calculate average rate (assuming INTEREST_RATE is constant)
            report["average_rate"] = INTEREST_RATE

            # Check if the loan is overdue
            last_payment_date = max(loan.payments, key=lambda x: x.date).date if loan.payments else "2000-01-01"
            today = f"{year}-{month:02d}-01"  # First day of the month
            if self.check_overdue(loan.loan_id, last_payment_date, today):
                report["overdue_count"] += 1
                report["total_late_fees"] += LATE_FEE

        return report

    def summarize_portfolio(self):
        summary = {
            "total_loans": len(self.loans),
            "total_principal": sum(loan.principal for loan in self.loans.values()),
            "average_rate": INTEREST_RATE,
            "overdue_count": sum(1 for loan in self.loans.values() if any(self.check_overdue(loan.loan_id, payment.date, datetime.now().strftime("%Y-%m-%d")) for payment in loan.payments)),
            "total_late_fees": sum(LATE_FEE for loan in self.loans.values() if any(self.check_overdue(loan.loan_id, payment.date, datetime.now().strftime("%Y-%m-%d")) for payment in loan.payments))
        }
        return summary

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
print(loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print(loan_system.get_loan(1).principal)

# Recording payments
loan_system.record_payment(1, 50000, "2023-10-01")
loan_system.record_payment(1, 60000, "2023-11-01", payment_type='PREPAYMENT')
print(loan_system.get_payment_history(1))

# Early repayment discount and payoff amount
remaining_balance = loan_system.get_payoff_amount(1)
early_repayment_discount = loan_system.calculate_early_repayment_discount(remaining_balance, 12)
print(f"Remaining Balance: {remaining_balance}")
print(f"Early Repayment Discount: {early_repayment_discount}")

# Check overdue and get overdue amount
is_overdue = loan_system.check_overdue(1, "2023-10-01", "2023-11-15")
overdue_amount = loan_system.get_overdue_amount(1)
print(f"Is Overdue: {is_overdue}")
print(f"Overdue Amount: {overdue_amount}")

# Generate payment schedule
payment_schedule = loan_system.generate_payment_schedule(1)
for payment in payment_schedule:
    print(payment)

# Get remaining balance after 6 months of payments
remaining_balance = loan_system.get_remaining_balance(1, 6)
print(f"Remaining Balance after 6 months: {remaining_balance}")

# Generate monthly report for January 2023
monthly_report = loan_system.generate_monthly_report(2023, 1)
print("Monthly Report for January 2023:", monthly_report)

# Summarize portfolio
portfolio_summary = loan_system.summarize_portfolio()
print("Portfolio Summary:", portfolio_summary)