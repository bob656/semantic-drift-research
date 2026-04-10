from dataclasses import dataclass

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

# 예제 사용 방법
if __name__ == "__main__":
    system = LoanSystem()
    
    # 대출 생성
    created = system.create_loan(1, "John Doe", 1000000, 24)
    print(f"Loan creation successful: {created}")
    
    # 월 납입액 계산
    try:
        payment = system.calculate_monthly_payment(1)
        print(f"Monthly payment for loan 1: {payment}원")
    except ValueError as e:
        print(e)
    
    # 연체료 적용
    system.apply_late_fee(1)
    loan = system.get_loan(1)
    print(f"Loan status after late fee: {loan.status}, New principal: {loan.principal}원")

    # 납부 기록 저장
    system.record_payment(1, 500000, "2023-10-01")
    system.record_payment(1, 500000, "2023-11-01", payment_type='EARLY')
    
    # 납부 이력 반환
    history = system.get_payment_history(1)
    for payment in history:
        print(f"Payment ID: {payment.payment_id}, Amount: {payment.amount}원, Date: {payment.date}, Type: {payment.type}")

    # 조기 상환 할인 계산
    remaining_balance = 500000
    remaining_months = 12
    discount = system.calculate_early_repayment_discount(remaining_balance, remaining_months)
    print(f"Early repayment discount for loan 1: {discount}원")

    # 현재 시점 완납 금액 반환
    payoff_amount = system.get_payoff_amount(1)
    print(f"Payoff amount for loan 1: {payoff_amount}원")