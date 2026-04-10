from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

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
    payments: List[Payment] = dataclass.field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: Dict[int, Loan] = {}
        self.payment_counter: int = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, 'active')
        return True

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return []
        return loan.payments

    def calculate_monthly_payment(self, loan_id: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        r = INTEREST_RATE / 12
        monthly_payment = loan.principal * r / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

    def calculate_early_repayment_discount(self, loan_id: int, remaining_balance: float, remaining_months: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return 0
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_interest = remaining_balance * monthly_interest_rate * remaining_months
        discount_amount = remaining_interest * 0.1
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_months = loan.months - len(loan.payments)
        remaining_interest = remaining_balance * monthly_interest_rate * remaining_months
        payoff_amount = remaining_balance + remaining_interest
        return payoff_amount

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return False
        last_payment_datetime = datetime.strptime(last_payment_date, '%Y-%m-%d')
        today_datetime = datetime.strptime(today, '%Y-%m-%d')
        delta = today_datetime - last_payment_datetime
        return delta.days >= 30

    def get_overdue_amount(self, loan_id: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        overdue_interest_rate = INTEREST_RATE * 1.5  # 연체료율은 기본 이자율의 1.5배로 가정
        overdue_months = (len(loan.payments) // 30) + 1  # 간단한 연체 월 수 계산 (예: 매월 납부 시)
        overdue_interest = remaining_balance * overdue_interest_rate * overdue_months
        late_fee = LATE_FEE * overdue_months
        total_overdue_amount = remaining_balance + overdue_interest + late_fee
        return total_overdue_amount

    def generate_payment_schedule(self, loan_id: int) -> Optional[List[Dict[str, float]]]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        
        monthly_payment = self.calculate_monthly_payment(loan_id)
        r = INTEREST_RATE / 12
        schedule = []
        remaining_principal = loan.principal
        for i in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = max(monthly_payment - interest_payment, MIN_PAYMENT)
            remaining_principal -= principal_payment
            
            schedule.append({
                'installment': i,
                'payment_amount': monthly_payment,
                'principal_payment': principal_payment,
                'interest_payment': interest_payment,
                'remaining_balance': remaining_principal
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        
        monthly_payment = self.calculate_monthly_payment(loan_id)
        r = INTEREST_RATE / 12
        remaining_principal = loan.principal
        for _ in range(paid_months):
            interest_payment = remaining_principal * r
            principal_payment = max(monthly_payment - interest_payment, MIN_PAYMENT)
            remaining_principal -= principal_payment
        
        return remaining_principal

# Example usage:
loan_system = LoanSystem()
if loan_system.create_loan(1, "John Doe", 1000000, 36):
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid term.")

monthly_payment = loan_system.calculate_monthly_payment(1)
if monthly_payment is not None:
    print(f"Monthly payment: {monthly_payment:.2f}원")
else:
    print("Failed to calculate monthly payment.")

loan_system.record_payment(1, 50000, '2023-10-01')
payment_history = loan_system.get_payment_history(1)
for payment in payment_history:
    print(f"Payment - ID: {payment.payment_id}, Amount: {payment.amount:.2f}원, Date: {payment.date}, Type: {payment.type}")

loan_system.apply_late_fee(1)
loan = loan_system.get_loan(1)
if loan:
    print(f"Loan details - ID: {loan.loan_id}, Borrower: {loan.borrower}, Principal: {loan.principal:.2f}원, Months: {loan.months}, Status: {loan.status}")
else:
    print("Loan not found.")

# 조기 상환 할인 계산
early_repayment_discount = loan_system.calculate_early_repayment_discount(1, 950000, 30)
print(f"Early repayment discount: {early_repayment_discount:.2f}원")

# 현재 시점 완납 금액 반환
payoff_amount = loan_system.get_payoff_amount(1)
if payoff_amount is not None:
    print(f"Payoff amount: {payoff_amount:.2f}원")
else:
    print("Failed to calculate payoff amount.")

# 연체 여부 확인
overdue_status = loan_system.check_overdue(1, '2023-09-01', '2023-10-15')
print(f"Overdue status: {overdue_status}")

# 연체 총액 반환
overdue_amount = loan_system.get_overdue_amount(1)
if overdue_amount is not None:
    print(f"Overdue amount: {overdue_amount:.2f}원")
else:
    print("Failed to calculate overdue amount.")

# 분할 납부 계획 생성
payment_schedule = loan_system.generate_payment_schedule(1)
for schedule in payment_schedule[:5]:  # 첫 5개 회차만 출력
    print(f"Installment: {schedule['installment']}, Payment Amount: {schedule['payment_amount']:.2f}원, Principal Payment: {schedule['principal_payment']:.2f}원, Interest Payment: {schedule['interest_payment']:.2f}원, Remaining Balance: {schedule['remaining_balance']:.2f}원")

# 납부 완료 월 수 기준 잔액 계산
remaining_balance = loan_system.get_remaining_balance(1, 10)
if remaining_balance is not None:
    print(f"Remaining balance after 10 months of payments: {remaining_balance:.2f}원")
else:
    print("Failed to calculate remaining balance.")