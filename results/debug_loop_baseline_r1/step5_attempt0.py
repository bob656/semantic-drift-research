from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE: float = 0.025
LATE_FEE: int = 5000
MAX_INSTALLMENTS: int = 36
MIN_PAYMENT: int = 10000
PENALTY_RATE: float = 0.015

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
    payments: list[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.payment_counter: int = 0

    # ... (기존 코드는 변경 없음)

    def generate_payment_schedule(self, loan_id: int) -> list[dict]:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        schedule = []
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        for i in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = monthly_payment - interest_payment
            remaining_principal -= principal_payment
            schedule.append({
                'installment_number': i,
                'payment_amount': round(monthly_payment),
                'principal_payment': round(principal_payment),
                'interest_payment': round(interest_payment),
                'remaining_balance': round(remaining_principal)
            })
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        for _ in range(paid_months):
            interest_payment = remaining_principal * r
            principal_payment = (remaining_principal + interest_payment) / MAX_INSTALLMENTS
            remaining_principal -= principal_payment
        return round(remaining_principal)

    def generate_monthly_report(self, year: int, month: int) -> dict:
        report = {
            'total_loans': 0,
            'total_principal': 0.0,
            'average_rate': 0.0,
            'overdue_count': 0,
            'total_late_fees': 0
        }

        for loan in self.loans.values():
            if not loan.payments:
                continue

            last_payment_date = datetime.strptime(loan.payments[-1].date, "%Y-%m-%d")
            expected_payment_date = datetime(year, month, 25)  # Assuming payment is due on the 25th of each month
            overdue = last_payment_date < expected_payment_date and loan.status != 'settled'

            report['total_loans'] += 1
            report['total_principal'] += loan.principal
            if overdue:
                report['overdue_count'] += 1
                report['total_late_fees'] += LATE_FEE

        if report['total_loans'] > 0:
            report['average_rate'] = INTEREST_RATE * 12 / report['total_loans']

        return report

    def summarize_portfolio(self) -> dict:
        summary = {
            'total_loans': len(self.loans),
            'total_principal': sum(loan.principal for loan in self.loans.values()),
            'average_rate': INTEREST_RATE * 12,
            'overdue_count': 0,
            'total_late_fees': 0
        }

        current_date = datetime.now()
        for loan in self.loans.values():
            if not loan.payments:
                continue

            last_payment_date = datetime.strptime(loan.payments[-1].date, "%Y-%m-%d")
            expected_payment_date = datetime(current_date.year, current_date.month, 25)  # Assuming payment is due on the 25th of each month
            overdue = last_payment_date < expected_payment_date and loan.status != 'settled'

            if overdue:
                summary['overdue_count'] += 1
                summary['total_late_fees'] += LATE_FEE

        return summary