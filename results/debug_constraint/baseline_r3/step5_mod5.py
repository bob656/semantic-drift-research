from dataclasses import dataclass
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
        self.payments = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False  # 거부
        new_loan = Loan(loan_id, borrower, principal, months, 'active')
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        loan = self.loans[loan_id]
        if loan.status == 'active':
            loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)
            loan.status = 'late'

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        payment_id = len(self.payments) + 1
        new_payment = Payment(payment_id, loan_id, amount, date, payment_type)
        self.payments[payment_id] = new_payment

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        return [payment for payment in self.payments.values() if payment.loan_id == loan_id]

    def calculate_early_repayment_discount(self, loan_id: int, remaining_balance: float) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        remaining_months = loan.months
        
        # 잔여 이자 계산
        remaining_interest = remaining_balance * r * remaining_months
        
        # 조기 상환 할인액 계산 (10% 할인)
        discount_amount = remaining_interest * 0.1
        
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        total_paid = sum(payment.amount for payment in self.payments.values() if payment.loan_id == loan_id)
        remaining_balance = max(0, loan.principal - total_paid)
        
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        last_payment = datetime.strptime(last_payment_date, '%Y-%m-%d')
        current_date = datetime.strptime(today, '%Y-%m-%d')
        overdue_days = (current_date - last_payment).days
        
        return overdue_days >= 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        total_due = loan.principal
        late_fee = LATE_FEE
        penalty_interest = loan.principal * PENALTY_RATE
        
        return total_due + late_fee + penalty_interest

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        schedule = []
        balance = loan.principal
        
        for month in range(1, loan.months + 1):
            interest = balance * r
            principal_payment = monthly_payment - interest
            new_balance = balance - principal_payment
            
            schedule.append({
                'month': month,
                'payment_amount': monthly_payment,
                'principal_part': principal_payment,
                'interest_part': interest,
                'balance': new_balance
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        
        balance = loan.principal
        
        for _ in range(paid_months):
            interest = balance * r
            principal_payment = monthly_payment - interest
            balance -= principal_payment
        
        return balance

    def generate_monthly_report(self, year: int, month: int) -> dict:
        report = {
            'total_loans': 0,
            'total_principal': 0,
            'average_rate': INTEREST_RATE * 100,
            'overdue_count': 0,
            'total_late_fees': 0
        }
        
        for loan in self.loans.values():
            report['total_loans'] += 1
            report['total_principal'] += loan.principal
            
            # 연체 여부 확인
            last_payment = max(self.payments.values(), key=lambda p: datetime.strptime(p.date, '%Y-%m-%d'), default=None)
            if last_payment and self.check_overdue(loan.loan_id, last_payment.date, f"{year}-{month}-01"):
                report['overdue_count'] += 1
                report['total_late_fees'] += LATE_FEE
        
        return report

    def summarize_portfolio(self) -> dict:
        summary = {
            'total_loans': len(self.loans),
            'total_principal': sum(loan.principal for loan in self.loans.values()),
            'average_rate': INTEREST_RATE * 100,
            'overdue_count': sum(1 for loan in self.loans.values() if any(
                self.check_overdue(loan.loan_id, payment.date, f"{datetime.now().year}-{datetime.now().month}-01")
                for payment in self.payments.values()
                if payment.loan_id == loan.loan_id
            )),
            'total_late_fees': sum(LATE_FEE for loan in self.loans.values() if any(
                self.check_overdue(loan.loan_id, payment.date, f"{datetime.now().year}-{datetime.now().month}-01")
                for payment in self.payments.values()
                if payment.loan_id == loan.loan_id
            ))
        }
        
        return summary

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 5000000, 24)
print(loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print(loan_system.get_loan(1).principal)

# Recording payment
loan_system.record_payment(1, 200000, '2023-01-01')
loan_system.record_payment(1, 300000, '2023-02-01', payment_type='PREPAYMENT')

# Getting payment history
print([payment.__dict__ for payment in loan_system.get_payment_history(1)])

# Early repayment discount calculation
discount = loan_system.calculate_early_repayment_discount(1, 4000000)
print(f"Early repayment discount: {discount}")

# Payoff amount calculation
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff amount: {payoff_amount}")

# Check overdue and get overdue amount
overdue_status = loan_system.check_overdue(1, '2023-01-01', '2023-04-01')
print(f"Overdue status: {overdue_status}")
if overdue_status:
    overdue_amount = loan_system.get_overdue_amount(1)
    print(f"Overdue amount: {overdue_amount}")

# Generate payment schedule
schedule = loan_system.generate_payment_schedule(1)
for entry in schedule:
    print(entry)

# Get remaining balance after 2 months of payments
remaining_balance = loan_system.get_remaining_balance(1, 2)
print(f"Remaining balance after 2 months: {remaining_balance}")

# Monthly report generation
monthly_report = loan_system.generate_monthly_report(2023, 4)
print("Monthly Report:", monthly_report)

# Portfolio summary
portfolio_summary = loan_system.summarize_portfolio()
print("Portfolio Summary:", portfolio_summary)