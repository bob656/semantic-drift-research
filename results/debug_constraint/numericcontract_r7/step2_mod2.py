from dataclasses import dataclass

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
    status: str
    payments: list[Payment] = None  # Initialize as empty list

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # To generate unique payment IDs

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, "active", [])
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return
        loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    # New methods for payment history management
    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return False
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1
        return True

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return []
        return loan.payments

    # New methods for early repayment calculation
    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            return 0.0
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        return remaining_balance

# 테스트 코드
loan_system = LoanSystem()
loan_system.create_loan(1, "Alice", 1000000, 24)
print("Monthly Payment:", loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print("Loan after late fee:", loan_system.get_loan(1).principal)

# Test payment history
loan_system.record_payment(1, 50000, "2023-10-01")
loan_system.record_payment(1, 60000, "2023-11-01", payment_type='EARLY')
print("Payment History:", [payment.amount for payment in loan_system.get_payment_history(1)])

# Test early repayment discount
remaining_balance = loan_system.get_payoff_amount(1)
discount = loan_system.calculate_early_repayment_discount(remaining_balance, 22)  # Assuming 22 months remaining
print(f"Early Repayment Discount: {discount}")