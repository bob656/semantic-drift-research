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

    def add_loan(self, loan):
        """대출 추가"""
        if loan.loan_id in self.loans:
            raise ValueError("Loan already exists")
        self.loans[loan.loan_id] = loan
        self.payment_history[loan.loan_id] = []

    def add_payment(self, payment):
        """납부 내역 추가"""
        if payment.loan_id not in self.loans:
            raise ValueError("Loan does not exist")
        self.payment_history[payment.loan_id].append(payment)

    def get_loan(self, loan_id):
        """대출 정보 조회"""
        return self.loans.get(loan_id)

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
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.check_overdue(loan_id, last_payment_date=today, today=today):
            overdue_amount = self.get_overdue_amount(loan_id)
            return remaining_balance + overdue_amount
        else:
            return remaining_balance

    def get_payoff_amount(self, loan_id: int) -> float:
        """대출 상환 금액 계산"""
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        remaining_balance = self.get_remaining_balance(loan_id, paid_months=0)
        return remaining_balance

    def generate_payment_schedule(self, loan_id):
        """전체 납부 계획표 생성"""
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        payment_schedule = []
        remaining_balance = loan.principal
        for month in range(1, loan.months + 1):
            interest_payment = remaining_balance * INTEREST_RATE / 12
            principal_payment = MIN_PAYMENT - interest_payment
            total_payment = interest_payment + principal_payment

            payment_schedule.append({
                'month': month,
                'total_payment': total_payment,
                'principal_payment': principal_payment,
                'interest_payment': interest_payment,
                'remaining_balance': remaining_balance - principal_payment
            })

            remaining_balance -= principal_payment

        return payment_schedule

    def get_remaining_balance(self, loan_id, paid_months):
        """납부 완료 월 수 기준 잔액 계산"""
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        remaining_balance = loan.principal
        for month in range(1, min(paid_months + 1, loan.months + 1)):
            interest_payment = remaining_balance * INTEREST_RATE / 12
            principal_payment = MIN_PAYMENT - interest_payment

            remaining_balance -= principal_payment

        return remaining_balance