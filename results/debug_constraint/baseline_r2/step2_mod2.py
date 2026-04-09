from dataclasses import dataclass

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000        # 연체료 (5000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000    # 최소 납입액 (10000원)
PENALTY_RATE = 0.015   # 연체 가산율 (1.5%)

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
    payments: list[Payment] = None  # Initialize with an empty list of payments

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # Unique identifier for each payment

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, 'active', [])
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan:
            return []
        return loan.payments

    # 추가된 메서드
    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        r = INTEREST_RATE / 12
        remaining_months = loan.months - len(loan.payments)
        interest_to_save = remaining_balance * r * remaining_months
        discount_amount = interest_to_save * 0.1  # 10% 할인
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0.0
        remaining_balance = loan.principal - sum(payment.amount for payment in loan.payments)
        return remaining_balance

# Example usage:
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 36)
print(loan_system.calculate_monthly_payment(1))  # Calculate monthly payment
loan_system.apply_late_fee(1)                  # Apply late fee
loan_system.record_payment(1, 50000, '2023-04-01')  # Record a payment
print(loan_system.get_loan(1))                 # Get loan details
print(loan_system.get_payment_history(1))        # Get payment history
print(loan_system.calculate_early_repayment(1, 950000))  # Calculate early repayment discount
print(loan_system.get_payoff_amount(1))         # Get payoff amount