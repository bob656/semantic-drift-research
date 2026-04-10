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

class LoanSystem:
    def __init__(self):
        self.loans = {}

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