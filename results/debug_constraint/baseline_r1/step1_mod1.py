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

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans[loan_id] = new_loan
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

    def get_loan(self, loan_id: int) -> Loan | None:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan := self.get_loan(loan_id):
            new_payment = Payment(payment_id=len(self.payment_history)+1, loan_id=loan_id, amount=amount, date=date, type=payment_type)
            if loan_id not in self.payment_history:
                self.payment_history[loan_id] = []
            self.payment_history[loan_id].append(new_payment)

    def get_payment_history(self, loan_id: int):
        return self.payment_history.get(loan_id, [])

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