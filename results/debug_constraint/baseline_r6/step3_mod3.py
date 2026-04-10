from dataclasses import dataclass, field
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
    status: str = field(default="active")
    payments: list[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.next_payment_id: int = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.next_payment_id += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        return loan.payments

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        remaining_months = len([p for p in loan.payments if p.type == 'REGULAR']) - len([p for p in loan.payments if p.amount > self.calculate_monthly_payment(loan_id)])
        residual_interest = remaining_balance * r * remaining_months
        early_repayment_discount = residual_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(p.amount for p in loan.payments if p.type == 'REGULAR')
        return max(total_paid + (loan.principal - total_paid), MIN_PAYMENT)

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        last_payment_datetime = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        delta = today_datetime - last_payment_datetime
        return delta.days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        overdue_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        overdue_interest_rate = INTEREST_RATE * 1.5
        overdue_days = sum((datetime.strptime(p.date, "%Y-%m-%d") - datetime.strptime(loan.payments[i-1].date, "%Y-%m-%d")).days for i, p in enumerate(loan.payments) if i > 0 and (datetime.strptime(p.date, "%Y-%m-%d") - datetime.strptime(loan.payments[i-1].date, "%Y-%m-%d")).days > 30)
        overdue_interest = loan.principal * overdue_interest_rate * (overdue_days / 365)
        
        return loan.principal + overdue_fee + overdue_interest

# 예시 사용
if __name__ == "__main__":
    system = LoanSystem()
    
    # 대출 생성
    created = system.create_loan(1, "Alice", 1000000, 24)
    print("Loan created:", created)  # True
    
    # 월 납입액 계산
    try:
        payment = system.calculate_monthly_payment(1)
        print("Monthly Payment:", payment)
    except ValueError as e:
        print(e)
    
    # 연체료 적용
    system.apply_late_fee(1)
    
    # 대출 조회
    loan = system.get_loan(1)
    if loan:
        print(f"Loan ID: {loan.loan_id}, Borrower: {loan.borrower}, Principal: {loan.principal}")
    
    # 납부 기록
    system.record_payment(1, 50000, "2023-10-01")
    
    # 납부 이력 조회
    payment_history = system.get_payment_history(1)
    for p in payment_history:
        print(f"Payment ID: {p.payment_id}, Date: {p.date}, Amount: {p.amount}, Type: {p.type}")
    
    # 조기 상환 할인액 계산
    try:
        discount = system.calculate_early_repayment(1, 900000)
        print("Early Repayment Discount:", discount)
    except ValueError as e:
        print(e)
    
    # 현재 시점 완납 금액 반환
    try:
        payoff_amount = system.get_payoff_amount(1)
        print("Payoff Amount:", payoff_amount)
    except ValueError as e:
        print(e)
        
    # 연체 여부 확인
    overdue_status = system.check_overdue(1, "2023-09-01", "2023-10-15")
    print("Overdue Status:", overdue_status)  # True
    
    # 연체 총액 반환
    try:
        overdue_amount = system.get_overdue_amount(1)
        print("Overdue Amount:", overdue_amount)
    except ValueError as e:
        print(e)