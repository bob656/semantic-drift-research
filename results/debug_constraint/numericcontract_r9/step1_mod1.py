from dataclasses import dataclass
from typing import Optional, List

# 핵심 수치 상수
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
    payments: List[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.payment_counter = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status="active")
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        return loan.payments

# 예시 사용
if __name__ == "__main__":
    loan_system = LoanSystem()
    
    # 대출 생성
    created = loan_system.create_loan(1, "John Doe", 500000, 24)
    print(f"Loan creation successful: {created}")
    
    # 월 납입액 계산
    try:
        monthly_payment = loan_system.calculate_monthly_payment(1)
        print(f"Monthly payment: {monthly_payment:.2f}원")
    except ValueError as e:
        print(e)
    
    # 연체료 적용
    try:
        loan_system.apply_late_fee(1)
        updated_loan = loan_system.get_loan(1)
        if updated_loan:
            print(f"Updated principal after late fee: {updated_loan.principal:.2f}원")
    except ValueError as e:
        print(e)

    # 납부 기록
    try:
        loan_system.record_payment(1, 50000, "2023-10-01", payment_type='REGULAR')
        payment_history = loan_system.get_payment_history(1)
        for payment in payment_history:
            print(f"Payment ID: {payment.payment_id}, Date: {payment.date}, Amount: {payment.amount}원")
    except ValueError as e:
        print(e)