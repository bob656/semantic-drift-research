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
    payments: list = None

    def __post_init__(self):
        self.payments = []

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_id_counter = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status='active')
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        late_fee_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee_amount

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        new_payment = Payment(payment_id=self.payment_id_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(new_payment)
        self.payment_id_counter += 1

    def get_payment_history(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        return loan.payments

# Example usage
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 1000000, 24)
if loan_created:
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid months.")

monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly payment for loan ID 1: {monthly_payment:.2f}원")

loan_system.apply_late_fee(1)
updated_loan = loan_system.get_loan(1)
print(f"Updated principal after late fee for loan ID 1: {updated_loan.principal:.2f}원")

loan_system.record_payment(1, 50000, '2023-01-01')
payment_history = loan_system.get_payment_history(1)
for payment in payment_history:
    print(f"Payment ID: {payment.payment_id}, Amount: {payment.amount:.2f}원, Date: {payment.date}, Type: {payment.type}")