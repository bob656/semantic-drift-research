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
    payments: list[Payment] = None  # Initialize as an empty list if not provided

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.next_payment_id = 1  # To generate unique payment IDs

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, 'active', [])
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        new_payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(new_payment)
        self.next_payment_id += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        return self.loans[loan_id].payments

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_months = len([p for p in loan.payments if p.type == 'REGULAR'])  # Assuming REGULAR payments are the only ones that count towards months
        
        residual_interest = remaining_balance * monthly_interest_rate * remaining_months
        early_repayment_discount = residual_interest * 0.1
        
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        total_paid = sum(p.amount for p in loan.payments)
        remaining_balance = max(0, loan.principal - total_paid)
        
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        overdue_days = (current_date - last_payment).days
        
        return overdue_days >= 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        total_paid = sum(p.amount for p in loan.payments)
        remaining_balance = max(0, loan.principal - total_paid)

        # Assuming the last payment date is the most recent payment
        if not loan.payments:
            return 0

        last_payment_date = datetime.strptime(loan.payments[-1].date, "%Y-%m-%d")
        current_date = datetime.now()
        overdue_days = (current_date - last_payment_date).days

        if overdue_days < 30:
            return 0

        # Calculate late fee
        late_fee = LATE_FEE

        # Calculate penalty
        penalty = remaining_balance * PENALTY_RATE

        # Calculate additional interest based on overdue days
        additional_interest = remaining_balance * INTEREST_RATE * (overdue_days / 365)

        return remaining_balance + late_fee + penalty + additional_interest

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        balance = loan.principal

        schedule = []
        for i in range(loan.months):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
            schedule.append({
                "month": i + 1,
                "payment_amount": monthly_payment,
                "principal_paid": principal_paid,
                "interest_paid": interest,
                "balance": balance
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        balance = loan.principal

        for _ in range(paid_months):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
        
        return balance