from dataclasses import dataclass
import datetime

# 핵심 수치 상수
INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015
OVERDUE_DAYS_THRESHOLD = 30

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

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}

    # ... 기존 메서드들 ...

    def check_overdue(self, loan_id, last_payment_date, today):
        """연체 여부 확인"""
        overdue_days = (datetime.datetime.strptime(today, '%Y-%m-%d') - datetime.datetime.strptime(last_payment_date, '%Y-%m-%d')).days
        return overdue_days >= OVERDUE_DAYS_THRESHOLD

    def get_overdue_amount(self, loan_id):
        """연체 총액 반환"""
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        last_payment_date = max(payment.date for payment in self.payment_history[loan_id]) if loan_id in self.payment_history else "2023-01-01"
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        if self.check_overdue(loan_id, last_payment_date, today):
            principal = sum(payment.amount for payment in self.payment_history[loan_id]) if loan_id in self.payment_history else 0
            overdue_amount = principal + LATE_FEE + (principal * PENALTY_RATE)
            return overdue_amount

        return 0

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        # 연체 여부 확인 및 연체 금액 계산
        if self.check_overdue(loan_id, last_payment_date=today, today=today):
            overdue_amount = self.get_overdue_amount(loan_id)
            return remaining_balance + overdue_amount
        else:
            return remaining_balance

    def get_payoff_amount(self, loan_id: int) -> float:
        # ... 기존 메서드 내용 ...