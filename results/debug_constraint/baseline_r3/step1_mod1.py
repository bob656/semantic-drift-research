from dataclasses import dataclass

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