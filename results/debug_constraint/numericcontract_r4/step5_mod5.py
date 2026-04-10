from dataclasses import dataclass
from datetime import datetime, timedelta

# 핵심 수치 상수
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
        self.loans: dict[int, Loan] = {}
        self.payments: dict[int, list[Payment]] = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months)
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        penalty = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty

    def get_loan(self, loan_id: int) -> Loan:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        return loan

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id=payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        
        if loan_id not in self.payments:
            self.payments[loan_id] = []
        self.payments[loan_id].append(payment)

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        return self.payments.get(loan_id, [])

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        remaining_months = loan.months - len(self.payments[loan_id]) if loan_id in self.payments else loan.months
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_interest = remaining_balance * monthly_interest_rate * remaining_months
        early_repayment_discount = remaining_interest * 0.1
        return early_repayment_discount

    def get_payoff_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(payment.amount for payment in self.payments.get(loan_id, []))
        remaining_balance = max(0, loan.principal - total_paid)
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        overdue_days = (current_date - last_payment).days
        return overdue_days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        total_paid = sum(payment.amount for payment in self.payments.get(loan_id, []))
        remaining_balance = max(0, loan.principal - total_paid)
        
        # 연체료
        late_fee = LATE_FEE
        
        # 가산이자 (연체일수 * 원금 * 일별 이자율)
        overdue_days = self.get_overdue_days(loan_id)
        daily_interest_rate = INTEREST_RATE / 365
        additional_interest = remaining_balance * overdue_days * daily_interest_rate
        
        return remaining_balance + late_fee + additional_interest

    def get_overdue_days(self, loan_id: int) -> int:
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        last_payment_date = datetime.strptime(self.get_last_payment_date(loan_id), "%Y-%m-%d")
        current_date = datetime.now()
        overdue_days = (current_date - last_payment_date).days
        return max(0, overdue_days)

    def get_last_payment_date(self, loan_id: int) -> str:
        payments = self.get_payment_history(loan_id)
        if not payments:
            raise ValueError("No payment history found")
        
        # 가장 최근의 날짜를 반환
        last_payment = max(payments, key=lambda p: datetime.strptime(p.date, "%Y-%m-%d"))
        return last_payment.date

    def generate_payment_schedule(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_balance = loan.principal
        schedule = []

        for month in range(loan.months):
            interest_payment = remaining_balance * monthly_interest_rate
            principal_payment = self.calculate_monthly_payment(loan_id) - interest_payment
            total_payment = interest_payment + principal_payment

            schedule.append({
                "month": month + 1,
                "total_payment": total_payment,
                "principal_payment": principal_payment,
                "interest_payment": interest_payment,
                "remaining_balance": remaining_balance - principal_payment
            })

            remaining_balance -= principal_payment

        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        loan = self.loans.get(loan_id)
        if not loan:
            raise ValueError("Loan not found")
        
        monthly_interest_rate = INTEREST_RATE / 12
        remaining_balance = loan.principal

        for month in range(paid_months):
            interest_payment = remaining_balance * monthly_interest_rate
            principal_payment = self.calculate_monthly_payment(loan_id) - interest_payment
            remaining_balance -= principal_payment

        return remaining_balance

    def generate_monthly_report(self, year: int, month: int):
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0
        }
        
        for loan in self.loans.values():
            if not (loan.status == "active"):
                continue
            
            report["total_loans"] += 1
            report["total_principal"] += loan.principal
            
            # 연체 여부 확인
            last_payment_date = self.get_last_payment_date(loan.loan_id)
            today = f"{year}-{month:02d}-01"
            if self.check_overdue(loan.loan_id, last_payment_date, today):
                report["overdue_count"] += 1
                report["total_late_fees"] += LATE_FEE
            
        if report["total_loans"] > 0:
            report["average_rate"] = INTEREST_RATE
        
        return report

    def summarize_portfolio(self):
        summary = {
            "total_active_loans": len([loan for loan in self.loans.values() if loan.status == "active"]),
            "total_principal_outstanding": sum(loan.principal for loan in self.loans.values()),
            "average_interest_rate": INTEREST_RATE,
            "max_installments": MAX_INSTALLMENTS
        }
        
        return summary

# 예시 사용 방법
loan_system = LoanSystem()
loan_id = 1
borrower = "John Doe"
principal = 1000000
months = 24

loan_system.create_loan(loan_id, borrower, principal, months)
loan_system.record_payment(loan_id, 50000, "2023-01-01")
loan_system.record_payment(loan_id, 60000, "2023-02-01")

# 연체 여부 확인
last_payment_date = "2023-02-01"
today = "2023-03-15"
is_overdue = loan_system.check_overdue(loan_id, last_payment_date, today)
print(f"Loan {loan_id} is overdue: {is_overdue}")

# 연체 총액 확인
overdue_amount = loan_system.get_overdue_amount(loan_id)
print(f"Overdue amount for loan {loan_id}: {overdue_amount}")

# 월간 보고서 생성
monthly_report = loan_system.generate_monthly_report(2023, 3)
print("Monthly Report:", monthly_report)

# 포트폴리오 요약 생성
portfolio_summary = loan_system.summarize_portfolio()
print("Portfolio Summary:", portfolio_summary)