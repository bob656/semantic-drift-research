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
    payments: list

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # Payment ID generator

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False  # 거부
        new_loan = Loan(loan_id, borrower, principal, months, "active", [])
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        if loan.status == "active":
            loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)
            loan.status = "late"

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        new_payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(new_payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> list:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        return loan.payments

    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        monthly_payment = self.calculate_monthly_payment(loan_id)
        remaining_payments = len([p for p in loan.payments if p.type == 'REGULAR'])  # Assuming REGULAR payments are counted
        remaining_balance = loan.principal - sum(p.amount for p in loan.payments if p.type == 'REGULAR')
        
        return remaining_balance + (remaining_balance * (INTEREST_RATE / 12) * remaining_payments)

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
print(loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print(loan_system.get_loan(1).principal)

# Recording payments
loan_system.record_payment(1, 50000, "2023-10-01")
loan_system.record_payment(1, 60000, "2023-11-01", payment_type='EXTRA')
print([payment.__dict__ for payment in loan_system.get_payment_history(1)])

# Early repayment discount
discount = loan_system.calculate_early_repayment_discount(loan_system.get_loan(1).principal, 24 - len(loan_system.get_payment_history(1)))
print(f"Early Repayment Discount: {discount}")

# Payoff amount
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff Amount: {payoff_amount}")