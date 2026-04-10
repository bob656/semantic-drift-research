from dataclasses import dataclass
from datetime import datetime, timedelta

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5,000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10,000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

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
        self.payment_counter = 0
        self.payments = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status='active')
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee
        loan.status = 'late'

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        self.payment_counter += 1
        new_payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        self.payments[self.payment_counter] = new_payment

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        return [payment for payment in self.payments.values() if payment.loan_id == loan_id]

    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        total_amount_paid = sum(payment.amount for payment in self.payments.values() if payment.loan_id == loan_id)
        remaining_balance = max(0, loan.principal - total_amount_paid)
        
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        delta = current_date - last_payment
        return delta.days >= 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        overdue_days = (datetime.now() - datetime.strptime(max(payment.date for payment in self.payments.values() if payment.loan_id == loan_id), "%Y-%m-%d")).days
        if overdue_days < 30:
            return 0
        
        late_fee = LATE_FEE
        penalty_interest = loan.principal * (PENALTY_RATE / 12) * (overdue_days // 30)
        total_overdue_amount = loan.principal + late_fee + penalty_interest
        return total_overdue_amount

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        remaining_principal = loan.principal
        payment_schedule = []

        for month in range(1, loan.months + 1):
            interest = remaining_principal * r
            principal_payment = monthly_payment - interest
            remaining_principal -= principal_payment
            payment_schedule.append({
                'month': month,
                'payment_amount': monthly_payment,
                'principal': principal_payment,
                'interest': interest,
                'balance': remaining_principal
            })

        return payment_schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        remaining_principal = loan.principal

        for _ in range(paid_months):
            interest = remaining_principal * r
            principal_payment = monthly_payment - interest
            remaining_principal -= principal_payment

        return remaining_principal

    def generate_monthly_report(self, year: int, month: int) -> dict:
        report = {
            'total_loans': 0,
            'total_principal': 0.0,
            'average_rate': 0.0,
            'overdue_count': 0,
            'total_late_fees': 0.0
        }
        
        for loan in self.loans.values():
            report['total_loans'] += 1
            report['total_principal'] += loan.principal
            
            if loan.status == 'late':
                report['overdue_count'] += 1
                overdue_days = (datetime.now() - datetime.strptime(max(payment.date for payment in self.payments.values() if payment.loan_id == loan.loan_id), "%Y-%m-%d")).days
                late_fee = LATE_FEE + (loan.principal * PENALTY_RATE) * (overdue_days // 30)
                report['total_late_fees'] += late_fee
        
        if report['total_loans'] > 0:
            report['average_rate'] = INTEREST_RATE / 12
        
        return report

    def summarize_portfolio(self) -> dict:
        summary = {
            'total_active_loans': 0,
            'total_principal_active': 0.0,
            'total_late_loans': 0,
            'total_principal_late': 0.0
        }
        
        for loan in self.loans.values():
            if loan.status == 'active':
                summary['total_active_loans'] += 1
                summary['total_principal_active'] += loan.principal
            elif loan.status == 'late':
                summary['total_late_loans'] += 1
                summary['total_principal_late'] += loan.principal
        
        return summary

# Example usage:
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 50000.0, 36)
loan_system.record_payment(1, 1200.0, "2023-09-01")
monthly_report = loan_system.generate_monthly_report(2023, 9)
portfolio_summary = loan_system.summarize_portfolio()

print("Monthly Report:", monthly_report)
print("Portfolio Summary:", portfolio_summary)