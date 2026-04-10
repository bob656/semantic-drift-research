from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 핵심 수치 상수 — 절대 변경 금지
INTEREST_RATE: float = 0.025
LATE_FEE: int = 5000
MAX_INSTALLMENTS: int = 36
MIN_PAYMENT: int = 10000
PENALTY_RATE: float = 0.015

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
    payments: list[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.payment_counter: int = 0

    # ... (기존 코드는 변경 없음)

    def generate_payment_schedule(self, loan_id: int) -> list[dict]:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        schedule = []
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        for i in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = monthly_payment - interest_payment
            remaining_principal -= principal_payment
            schedule.append({
                'installment_number': i,
                'payment_amount': round(monthly_payment),
                'principal_payment': round(principal_payment),
                'interest_payment': round(interest_payment),
                'remaining_balance': round(remaining_principal)
            })
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        for _ in range(paid_months):
            interest_payment = remaining_principal * r
            principal_payment = (remaining_principal + interest_payment) / MAX_INSTALLMENTS
            remaining_principal -= principal_payment
        return round(remaining_principal)