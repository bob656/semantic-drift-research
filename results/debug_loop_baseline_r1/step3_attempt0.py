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

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status='active')
        self.loans[loan_id] = new_loan
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
        # Assuming the principal is reduced by the late fee amount
        loan.principal += late_fee_amount

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        new_payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(new_payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        return self.loans[loan_id].payments

    # 추가된 메서드
    def calculate_early_repayment(self, loan_id: int, remaining_balance: float, remaining_months: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        r = INTEREST_RATE / 12
        remaining_interest = remaining_balance * r * remaining_months
        early_repayment_discount = remaining_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        monthly_payment = self.calculate_monthly_payment(loan_id)
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        return remaining_balance + (remaining_balance * INTEREST_RATE / 12) * (MAX_INSTALLMENTS - len(loan.payments))

    # 연체 감지 및 알림 조건 기능 추가
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
        overdue_days = 0
        for payment in reversed(loan.payments):
            last_payment_date = datetime.strptime(payment.date, "%Y-%m-%d")
            break
        
        if len(loan.payments) == 0:
            return 0

        current_date = datetime.now()
        if (current_date - last_payment_date).days > 30:
            overdue_days = (current_date - last_payment_date).days - 30
            late_fee = LATE_FEE * overdue_days
            penalty_interest = loan.principal * PENALTY_RATE * overdue_days
            return loan.principal + late_fee + penalty_interest
        
        return 0