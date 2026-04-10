from dataclasses import dataclass
from datetime import datetime, timedelta

# 핵심 수치 상수
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

@dataclass
class Loan:
    loan_id: int
    borrower: str
    principal: float
    months: int
    status: str

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
        self.payment_counter = 0

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        loan = Loan(loan_id=loan_id, borrower=borrower, principal=principal, months=months, status="active")
        self.loans[loan_id] = loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        if loan.status == "active":
            loan.principal += LATE_FEE + (loan.principal * PENALTY_RATE)
            loan.status = "late"

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        self.payment_counter += 1
        payment = Payment(payment_id=self.payment_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        # 여기서는 실제로 납부 이력을 저장하는 로직을 추가해야 합니다.
        # 예를 들어, 각 Loan 객체에 payments라는 리스트를 추가하여 관리할 수 있습니다.
        if 'payments' not in self.loans[loan_id]:
            self.loans[loan_id].payments = []
        self.loans[loan_id].payments.append(payment)

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        return getattr(self.loans[loan_id], 'payments', [])

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        remaining_months = loan.months
        interest_to_save = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = interest_to_save * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        loan = self.loans[loan_id]
        remaining_balance = loan.principal
        for payment in getattr(loan, 'payments', []):
            remaining_balance -= payment.amount
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        
        # 날짜 파싱
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        
        # 30일 이상 지남 확인
        if (current_date - last_payment).days >= 30:
            return True
        return False

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        
        loan = self.loans[loan_id]
        overdue_principal = loan.principal  # 미납 원금
        overdue_interest = overdue_principal * INTEREST_RATE  # 연체료
        overdue_penalty = overdue_principal * PENALTY_RATE  # 가산 이자
        
        return overdue_principal + overdue_interest + overdue_penalty

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        
        loan = self.loans[loan_id]
        schedule = []
        remaining_balance = loan.principal
        r = INTEREST_RATE / 12
        
        for month in range(1, loan.months + 1):
            interest_payment = remaining_balance * r
            principal_payment = max(self.calculate_monthly_payment(loan_id) - interest_payment, MIN_PAYMENT)
            total_payment = interest_payment + principal_payment
            remaining_balance -= principal_payment
            
            schedule.append({
                'Installment Number': month,
                'Payment Amount': total_payment,
                'Principal Payment': principal_payment,
                'Interest Payment': interest_payment,
                'Remaining Balance': remaining_balance
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID not found.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        remaining_balance = loan.principal
        
        for _ in range(paid_months):
            interest_payment = remaining_balance * r
            principal_payment = max(self.calculate_monthly_payment(loan_id) - interest_payment, MIN_PAYMENT)
            remaining_balance -= principal_payment
        
        return remaining_balance

    def generate_monthly_report(self, year: int, month: int):
        report = {
            'total_loans': 0,
            'total_principal': 0.0,
            'average_rate': 0.0,
            'overdue_count': 0,
            'total_late_fees': 0.0
        }
        
        for loan in self.loans.values():
            report['total_loans'] += 1
            report['total_principal'] += loan.principal
            
            # 연체 여부 확인
            if getattr(loan, 'payments', []):
                last_payment = datetime.strptime(loan.payments[-1].date, "%Y-%m-%d")
                current_date = datetime(year=year, month=month, day=28)
                if (current_date - last_payment).days >= 30:
                    report['overdue_count'] += 1
                    report['total_late_fees'] += LATE_FEE + (loan.principal * PENALTY_RATE)

        # 평균 이율 계산
        report['average_rate'] = INTEREST_RATE
        
        return report

    def summarize_portfolio(self):
        summary = {
            'total_loans': len(self.loans),
            'total_principal': sum(loan.principal for loan in self.loans.values()),
            'average_rate': INTEREST_RATE,
            'overdue_count': sum(1 for loan in self.loans.values() if getattr(loan, 'payments', []) and
                                (datetime.strptime(loan.payments[-1].date, "%Y-%m-%d") + timedelta(days=30)) < datetime.now()),
            'total_late_fees': sum(LATE_FEE + (loan.principal * PENALTY_RATE) for loan in self.loans.values()
                                 if getattr(loan, 'payments', []) and
                                 (datetime.strptime(loan.payments[-1].date, "%Y-%m-%d") + timedelta(days=30)) < datetime.now())
        }
        
        return summary

# 예시 사용
loan_system = LoanSystem()
loan_system.create_loan(1, "John Doe", 1000000, 24)
monthly_payment = loan_system.calculate_monthly_payment(1)
print(f"Monthly Payment: {monthly_payment}")
loan_system.record_payment(1, monthly_payment, '2023-01-01')
payment_history = loan_system.get_payment_history(1)
print(f"Payment History: {payment_history}")

early_repayment_discount = loan_system.calculate_early_repayment(1, 950000)
print(f"Early Repayment Discount: {early_repayment_discount}")
payoff_amount = loan_system.get_payoff_amount(1)
print(f"Payoff Amount: {payoff_amount}")

# 연체 감지 및 알림 조건 기능 테스트
is_overdue = loan_system.check_overdue(1, '2023-01-01', '2023-02-15')
print(f"Is Overdue: {is_overdue}")
overdue_amount = loan_system.get_overdue_amount(1)
print(f"Overdue Amount: {overdue_amount}")

# 월간 보고서 생성
monthly_report = loan_system.generate_monthly_report(2023, 2)
print(f"Monthly Report: {monthly_report}")

# 포트폴리오 요약
portfolio_summary = loan_system.summarize_portfolio()
print(f"Portfolio Summary: {portfolio_summary}")