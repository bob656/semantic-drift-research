from dataclasses import dataclass

# 핵심 수치 상수
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
        self.payment_counter = 0

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status="active")
        self.loans[loan_id] = loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        if loan.status == "active":
            loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)
            loan.status = "late"

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        self.payment_counter += 1
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        # 여기서는 실제로 납부 이력을 저장하는 로직을 추가해야 합니다.
        # 예를 들어, 각 Loan 객체에 payments라는 리스트를 추가하여 관리할 수 있습니다.
        if 'payments' not in self.loans[loan_id]:
            self.loans[loan_id].payments = []
        self.loans[loan_id].payments.append(payment)

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        return getattr(self.loans[loan_id], 'payments', [])

# 예시 사용
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly Payment: {monthly_payment}")
loan_system.record_payment(1, monthly_payment, '2023-01-01')
payment_history = loan_system.get_payment_history(1)
print(f"Payment History: {payment_history}")