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

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans[loan_id] = new_loan
        self.payment_history[loan_id] = []
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan does not exist.")
        
        payment = Payment(payment_id=len(self.payment_history[loan_id]) + 1,
                          loan_id=loan_id,
                          amount=amount,
                          date=date,
                          type=payment_type)
        
        self.payment_history[loan_id].append(payment)

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan does not exist.")
        
        return self.payment_history.get(loan_id, [])

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

# Example usage
if __name__ == "__main__":
    system = LoanSystem()
    
    # Create a loan
    created = system.create_loan(1, "Alice", 500000, 36)
    print(f"Loan created: {created}")
    
    # Calculate monthly payment
    try:
        payment = system.calculate_monthly_payment(1)
        print(f"Monthly payment: {payment:.2f}원")
    except ValueError as e:
        print(e)
    
    # Apply late fee
    system.apply_late_fee(1)
    loan = system.get_loan(1)
    print(f"Loan principal after late fee: {loan.principal:.2f}원")

    # Record a payment
    system.record_payment(1, 30000, "2024-01-15", 'REGULAR')
    payment_history = system.get_payment_history(1)
    print(f"Payment history for loan ID 1: {payment_history}")