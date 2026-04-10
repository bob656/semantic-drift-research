from dataclasses import dataclass, field

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