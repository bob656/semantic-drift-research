from dataclasses import dataclass

# 핵심 수치 상수 (절대 변경 금지)
INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015

@dataclass
class Loan:
    loan_id: int
    borrower: str
    principal: float
    months: int
    status: str = "active"

class LoanSystem:
    def __init__(self):
        self.loans = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months)
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        r = INTEREST_RATE / 12
        monthly_payment = (self.loans[loan_id].principal * r) / (1 - (1 + r) ** (-self.loans[loan_id].months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        loan = self.loans[loan_id]
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist")
        
        return self.loans[loan_id]

# Example usage
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 500000, 30)
if loan_created:
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid months.")

monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly Payment: {monthly_payment:.2f}원")

loan_system.apply_late_fee(1)
updated_loan = loan_system.get_loan(1)
print(f"Updated Principal after late fee: {updated_loan.principal:.2f}원")