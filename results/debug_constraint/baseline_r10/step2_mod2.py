from dataclasses import dataclass

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
    status: str = "active"
    payments: list[Payment] = None  # 납부 이력 저장

    def __post_init__(self):
        if self.payments is None:
            self.payments = []

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.next_payment_id = 1  # Payment ID를 위한 전역 변수

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months)
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        late_fee = LATE_FEE + loan.principal * PENALTY_RATE
        # 여기서 실제로 연체료를 추가하는 로직을 구현해야 합니다.
        # 예를 들어, loan.principal += late_fee 와 같이 잔액에 연체료를 더할 수 있습니다.

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        new_payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(new_payment)
        self.next_payment_id += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        return loan.payments

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        r = INTEREST_RATE / 12
        remaining_months = len([p for p in loan.payments if p.type == 'REGULAR'])
        remaining_interest = remaining_balance * r * remaining_months
        early_repayment_discount = remaining_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is not active")
        
        total_paid = sum(p.amount for p in loan.payments)
        remaining_balance = loan.principal - total_paid
        return remaining_balance + (remaining_balance * INTEREST_RATE / 12 * len([p for p in loan.payments if p.type == 'REGULAR']))