from dataclasses import dataclass

# 핵심 수치 상수 — 절대 변경 금지
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

@dataclass
class Payment:
    payment_id: int
    loan_id: int
    amount: float
    date: str
    type: str

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_counter = 1  # Unique identifier for payments

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        late_fee_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee_amount

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        # Assuming a simple list to store payments for each loan
        if hasattr(self.loans[loan_id], 'payments'):
            self.loans[loan_id].payments.append(Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type))
        else:
            self.loans[loan_id].payments = [Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)]
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        return getattr(self.loans[loan_id], 'payments', [])

    # 추가된 메서드
    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        loan = self.loans[loan_id]
        # Assuming the last payment recorded is the most recent
        payments = getattr(loan, 'payments', [])
        if not payments:
            return loan.principal
        last_payment = max(payments, key=lambda x: x.payment_id)
        remaining_balance = loan.principal - sum(payment.amount for payment in payments if payment.date <= last_payment.date)
        return remaining_balance

# Example usage
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
print(loan_system.calculate_monthly_payment(1))
loan_system.apply_late_fee(1)
print(loan_system.get_loan(1).principal)

# Recording payments
loan_system.record_payment(1, 50000, "2023-10-01")
loan_system.record_payment(1, 60000, "2023-11-01", payment_type='PREPAYMENT')
print(loan_system.get_payment_history(1))

# Early repayment discount and payoff amount
remaining_balance = loan_system.get_payoff_amount(1)
early_repayment_discount = loan_system.calculate_early_repayment_discount(remaining_balance, 12)
print(f"Remaining Balance: {remaining_balance}")
print(f"Early Repayment Discount: {early_repayment_discount}")