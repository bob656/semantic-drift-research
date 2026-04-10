from typing import List, Optional

INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015

class Loan:
    def __init__(self, loan_id: int, borrower: str, principal: float, months: int, status: str):
        self.loan_id = loan_id
        self.borrower = borrower
        self.principal = principal
        self.months = months
        self.status = status

class LoanSystem:
    def __init__(self):
        self.loans: List[Loan] = []

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans.append(new_loan)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> Optional[float]:
        for loan in self.loans:
            if loan.loan_id == loan_id and loan.status == "active":
                r = INTEREST_RATE / 12
                monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
                return max(monthly_payment, MIN_PAYMENT)
        return None

    def apply_late_fee(self, loan_id: int):
        for loan in self.loans:
            if loan.loan_id == loan_id and loan.status == "active":
                late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
                loan.principal += late_fee
                break

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        for loan in self.loans:
            if loan.loan_id == loan_id:
                return loan
        return None

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 100000, 36)
print(loan_system.calculate_monthly_payment(1))  # Should print the calculated monthly payment or MIN_PAYMENT if lower
loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
if loan:
    print(f"Loan ID: {loan.loan_id}, Borrower: {loan.borrower}, Principal: {loan.principal}, Months: {loan.months}, Status: {loan.status}")