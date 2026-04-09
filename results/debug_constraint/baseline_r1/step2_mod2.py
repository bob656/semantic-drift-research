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
    status: str

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}

    # ... 기존 메서드들 ...

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        remaining_months = MAX_INSTALLMENTS - len(self.payment_history[loan_id]) if loan_id in self.payment_history else loan.months
        residual_interest = remaining_balance * INTEREST_RATE / 12 * remaining_months
        discount_amount = residual_interest * 0.1
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        monthly_payment = self.calculate_monthly_payment(loan_id)
        remaining_balance = sum(monthly_payment for _ in range(MAX_INSTALLMENTS - len(self.payment_history[loan_id])))
        return remaining_balance

# Example usage
loan_system = LoanSystem()
loan_id = 1
if loan_system.create_loan(loan_id, "John Doe", 1000000, 36):
    print("Loan created successfully")
else:
    print("Failed to create loan")

monthly_payment = loan_system.calculate_monthly_payment(loan_id)
print(f"Monthly payment: {monthly_payment}")

loan_system.apply_late_fee(loan_id)
late_fee_loan = loan_system.get_loan(loan_id)
if late_fee_loan:
    print(f"Loan after applying late fee: Principal - {late_fee_loan.principal}")

# Record a payment
loan_system.record_payment(loan_id, 30000, "2024-01-01")

# Get payment history
payment_history = loan_system.get_payment_history(loan_id)
print("Payment History:", payment_history)

# Calculate early repayment discount and payoff amount
early_repayment_discount = loan_system.calculate_early_repayment(loan_id, 500000) # 예시 잔여 이자 계산
payoff_amount = loan_system.get_payoff_amount(loan_id)
print(f"Early Repayment Discount: {early_repayment_discount}")
print(f"Payoff Amount: {payoff_amount}")