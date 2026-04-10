from dataclasses import dataclass
from datetime import datetime, timedelta

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
    overdue_days: int = 0  # 연체일수 추가

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

    # 추가된 메서드
    def calculate_early_repayment_discount(self, loan_id: int, remaining_balance: float, remaining_months: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_interest = remaining_balance * monthly_interest_rate * remaining_months
        discount_amount = remaining_interest * 0.1
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        remaining_balance = loan.principal - sum(payment.amount for payment in loan.payments)
        return remaining_balance

    # 연체 감지 및 알림 조건 기능 추가
    def check_overdue(self, loan_id: int, last_payment_date: str, today: str):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        last_payment_datetime = datetime.strptime(last_payment_date, '%Y-%m-%d')
        today_datetime = datetime.strptime(today, '%Y-%m-%d')
        overdue_days = (today_datetime - last_payment_datetime).days
        
        if overdue_days > 30:
            loan.overdue_days = overdue_days
            self.apply_late_fee(loan_id)
        else:
            loan.overdue_days = 0

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            raise ValueError("Loan does not exist or is inactive.")
        
        overdue_principal = max(0, loan.principal - sum(payment.amount for payment in loan.payments))
        late_fee_amount = LATE_FEE + (overdue_principal * PENALTY_RATE)
        interest_rate = INTEREST_RATE / 12
        additional_interest = overdue_principal * interest_rate * loan.overdue_days
        
        return overdue_principal + late_fee_amount + additional_interest

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

# 조기 상환 할인 계산 예제
remaining_balance = 800000
remaining_months = 12
discount_amount = loan_system.calculate_early_repayment_discount(1, remaining_balance, remaining_months)
print(f"Early repayment discount for loan ID 1: {discount_amount:.2f}원")

# 현재 시점 완납 금액 반환 예제
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff amount for loan ID 1: {payoff_amount:.2f}원")

# 연체 감지 및 알림 조건 기능 테스트
loan_system.check_overdue(1, '2023-01-01', '2023-04-15')
overdue_amount = loan_system.get_overdue_amount(1)
print(f"Overdue amount for loan ID 1: {overdue_amount:.2f}원")