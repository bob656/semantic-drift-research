from dataclasses import dataclass

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
    status: str = "Active"
    payments: list[Payment] = None

    def __post_init__(self):
        if self.payments is None:
            self.payments = []

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # Unique identifier for payments

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months)
        self.loans[loan_id] = loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        # Assuming the fee is deducted from the principal for simplicity
        loan.principal += late_fee

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        return loan.payments

    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * INTEREST_RATE / 12 * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        # Calculate the total amount to be paid off considering remaining balance and interest
        remaining_balance = loan.principal - sum(payment.amount for payment in loan.payments)
        remaining_months = loan.months - len(loan.payments)
        monthly_interest = remaining_balance * INTEREST_RATE / 12
        total_interest = monthly_interest * remaining_months
        payoff_amount = remaining_balance + total_interest
        return payoff_amount

# Example usage:
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 500000, 24)
if loan_created:
    print("Loan created successfully")
else:
    print("Failed to create loan")

monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly payment: {monthly_payment}")

loan_system.apply_late_fee(1)
late_fee_applied_loan = loan_system.get_loan(1)
print(f"Updated principal after late fee: {late_fee_applied_loan.principal}")

# Record a payment
loan_system.record_payment(1, 20000, "2023-10-01")

# Get payment history
payment_history = loan_system.get_payment_history(1)
print("Payment History:")
for payment in payment_history:
    print(f"ID: {payment.payment_id}, Amount: {payment.amount}, Date: {payment.date}, Type: {payment.type}")

# Calculate early repayment discount
remaining_balance = late_fee_applied_loan.principal - sum(payment.amount for payment in loan.payments)
remaining_months = 24 - len(loan.payments)  # Assuming the loan was created with 24 months initially
discount = loan_system.calculate_early_repayment_discount(remaining_balance, remaining_months)
print(f"Early repayment discount: {discount}")

# Get payoff amount
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff amount: {payoff_amount}")