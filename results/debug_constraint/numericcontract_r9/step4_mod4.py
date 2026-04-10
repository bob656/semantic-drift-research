from dataclasses import dataclass, field
from typing import Optional, List
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
    payments: List[Payment] = field(default_factory=list)

class LoanSystem:
    def __init__(self):
        self.loans: dict[int, Loan] = {}
        self.payment_counter = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status="active")
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

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        return self.loans.get(loan_id)

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_counter += 1

    def get_payment_history(self, loan_id: int) -> List[Payment]:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        return loan.payments

    def calculate_early_repayment_discount(self, remaining_balance: float, remaining_months: int) -> float:
        remaining_interest = remaining_balance * INTEREST_RATE * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = max(0, loan.principal - total_paid)
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        last_payment_datetime = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_datetime = datetime.strptime(today, "%Y-%m-%d")
        overdue_days = (today_datetime - last_payment_datetime).days
        
        return overdue_days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_principal = max(0, loan.principal - total_paid)
        overdue_amount = remaining_principal + LATE_FEE
        
        # 가산 이자 계산 (단순화된 예시: 연체일수에 따라 일정 비율의 이자를 부과)
        last_payment_date = loan.payments[-1].date if loan.payments else "2023-01-01"  # 초기 납부일 설정 필요
        today = datetime.now().strftime("%Y-%m-%d")
        
        if self.check_overdue(loan_id, last_payment_date, today):
            overdue_days = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(last_payment_date, "%Y-%m-%d")).days
            additional_interest = remaining_principal * PENALTY_RATE * overdue_days / 365
            overdue_amount += additional_interest
        
        return overdue_amount

    def generate_payment_schedule(self, loan_id: int) -> List[dict]:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        schedule = []
        remaining_principal = loan.principal
        monthly_payment = self.calculate_monthly_payment(loan_id)
        
        for month in range(1, loan.months + 1):
            interest = remaining_principal * INTEREST_RATE / 12
            principal_payment = max(monthly_payment - interest, MIN_PAYMENT - interest)
            
            if remaining_principal <= principal_payment:
                principal_payment = remaining_principal
                monthly_payment = principal_payment + interest
            
            schedule.append({
                "month": month,
                "payment_amount": round(monthly_payment),
                "principal_payment": round(principal_payment),
                "interest_payment": round(interest),
                "remaining_balance": round(remaining_principal - principal_payment)
            })
            
            remaining_principal -= principal_payment
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> float:
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        remaining_principal = loan.principal
        monthly_payment = self.calculate_monthly_payment(loan_id)
        
        for _ in range(paid_months):
            interest = remaining_principal * INTEREST_RATE / 12
            principal_payment = max(monthly_payment - interest, MIN_PAYMENT - interest)
            
            if remaining_principal <= principal_payment:
                principal_payment = remaining_principal
            
            remaining_principal -= principal_payment
        
        return round(remaining_principal)

# 예시 사용
if __name__ == "__main__":
    loan_system = LoanSystem()
    
    # 대출 생성
    created = loan_system.create_loan(1, "John Doe", 500000, 24)
    print(f"Loan creation successful: {created}")
    
    # 월 납입액 계산
    try:
        monthly_payment = loan_system.calculate_monthly_payment(1)
        print(f"Monthly payment: {monthly_payment:.2f}원")
    except ValueError as e:
        print(e)
    
    # 연체료 적용
    try:
        loan_system.apply_late_fee(1)
        updated_loan = loan_system.get_loan(1)
        if updated_loan:
            print(f"Updated principal after late fee: {updated_loan.principal:.2f}원")
    except ValueError as e:
        print(e)

    # 납부 기록
    try:
        loan_system.record_payment(1, 50000, "2023-10-01", payment_type='REGULAR')
        payment_history = loan_system.get_payment_history(1)
        for payment in payment_history:
            print(f"Payment ID: {payment.payment_id}, Date: {payment.date}, Amount: {payment.amount}원")
    except ValueError as e:
        print(e)

    # 조기 상환 할인 계산
    try:
        remaining_balance = loan_system.get_payoff_amount(1)
        discount = loan_system.calculate_early_repayment_discount(remaining_balance, 20)  # 예: 남은 기간이 20개월
        print(f"Early repayment discount: {discount:.2f}원")
    except ValueError as e:
        print(e)

    # 현재 시점 완납 금액 반환
    try:
        payoff_amount = loan_system.get_payoff_amount(1)
        print(f"Payoff amount at this point: {payoff_amount:.2f}원")
    except ValueError as e:
        print(e)

    # 연체 여부 확인 및 연체 총액 계산
    try:
        overdue = loan_system.check_overdue(1, "2023-09-01", datetime.now().strftime("%Y-%m-%d"))
        if overdue:
            print("This loan is overdue.")
            overdue_amount = loan_system.get_overdue_amount(1)
            print(f"Overdue amount: {overdue_amount:.2f}원")
        else:
            print("This loan is not overdue.")
    except ValueError as e:
        print(e)

    # 납부 계획 생성
    try:
        payment_schedule = loan_system.generate_payment_schedule(1)
        for entry in payment_schedule:
            print(f"Month: {entry['month']}, Payment Amount: {entry['payment_amount']}원, "
                  f"Principal Payment: {entry['principal_payment']}원, Interest Payment: {entry['interest_payment']}원, "
                  f"Remaining Balance: {entry['remaining_balance']}원")
    except ValueError as e:
        print(e)

    # 남은 잔액 계산
    try:
        remaining_balance = loan_system.get_remaining_balance(1, 5)
        print(f"Remaining balance after 5 payments: {remaining_balance}원")
    except ValueError as e:
        print(e)