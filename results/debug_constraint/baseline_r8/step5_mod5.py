from dataclasses import dataclass, field
from datetime import datetime, timedelta

# 핵심 수치 상수
INTEREST_RATE = 0.025  # 연이율 (2.5%)
LATE_FEE = 5000  # 연체료 (5,000원)
MAX_INSTALLMENTS = 36  # 최대 할부 개월 수 (36개월)
MIN_PAYMENT = 10000  # 최소 납입액 (10,000원)
PENALTY_RATE = 0.015  # 연체 가산율 (1.5%)

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

    def remaining_months(self) -> int:
        """대출의 잔여 월 수를 계산합니다."""
        return max(0, self.months - len(self.payments))

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_id_counter = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False  # 최대 할부 개월 수를 초과하면 거부
        self.loans[loan_id] = Loan(loan_id, borrower, principal, months, "active")
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12  # 월 이율
        monthly_payment = (loan.principal * r) / (1 - (1 + r)**(-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        penalty_amount = LATE_FEE + loan.principal * PENALTY_RATE
        loan.principal += penalty_amount
        loan.status = "late"

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        payment = Payment(payment_id=self.payment_id_counter, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.payment_id_counter += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        return loan.payments

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        return self.loans[loan_id]

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float) -> float:
        """조기 상환 시 절감 이자 계산"""
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12  # 월 이율
        remaining_months = loan.remaining_months()
        remaining_interest = remaining_balance * r * remaining_months
        discount_amount = remaining_interest * 0.1  # 10% 할인
        return discount_amount

    def get_payoff_amount(self, loan_id: int) -> float:
        """현재 시점 완납 금액 반환"""
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        remaining_balance = loan.principal
        for payment in loan.payments:
            remaining_balance -= payment.amount
        return max(0, remaining_balance)

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_date = datetime.strptime(today, "%Y-%m-%d")
        return (current_date - last_payment).days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        overdue_interest = loan.principal * INTEREST_RATE
        late_fee = LATE_FEE
        penalty_amount = loan.principal * PENALTY_RATE
        
        return loan.principal + overdue_interest + late_fee + penalty_amount

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        schedule = []
        r = INTEREST_RATE / 12  # 월 이율
        remaining_principal = loan.principal

        for month in range(1, loan.months + 1):
            interest_payment = remaining_principal * r
            principal_payment = max(self.calculate_monthly_payment(loan_id) - interest_payment, MIN_PAYMENT)
            total_payment = interest_payment + principal_payment
            balance = remaining_principal - principal_payment
            
            schedule.append({
                "회차번호": month,
                "납입액": total_payment,
                "원금 부분": principal_payment,
                "이자 부분": interest_payment,
                "잔액": balance
            })
            
            remaining_principal = balance

        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("대출이 존재하지 않습니다.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12  # 월 이율
        remaining_principal = loan.principal

        for month in range(1, paid_months + 1):
            interest_payment = remaining_principal * r
            principal_payment = max(self.calculate_monthly_payment(loan_id) - interest_payment, MIN_PAYMENT)
            balance = remaining_principal - principal_payment
            
            remaining_principal = balance

        return balance

    def generate_monthly_report(self, year: int, month: int):
        """해당 월 대출 현황 딕셔너리 반환"""
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }

        for loan in self.loans.values():
            # 대출이 해당 월에 생성된 경우만 포함
            if len(loan.payments) > 0:
                first_payment_date = datetime.strptime(loan.payments[0].date, "%Y-%m-%d")
                payment_month = first_payment_date.month
                payment_year = first_payment_date.year

                if payment_year == year and payment_month == month:
                    report["total_loans"] += 1
                    report["total_principal"] += loan.principal

                    # 연체 여부 확인
                    last_payment_date = datetime.strptime(loan.payments[-1].date, "%Y-%m-%d")
                    today = datetime.today()
                    if (today - last_payment_date).days > 30:
                        report["overdue_count"] += 1
                        report["total_late_fees"] += LATE_FEE

        # 평균 이자율 계산
        if report["total_loans"] > 0:
            report["average_rate"] = INTEREST_RATE / 12 * 100  # 월 이율을 퍼센트로 변환

        return report

    def summarize_portfolio(self):
        """전체 포트폴리오 요약 반환"""
        summary = {
            "total_loans": len(self.loans),
            "total_principal": sum(loan.principal for loan in self.loans.values()),
            "average_rate": INTEREST_RATE / 12 * 100,  # 월 이율을 퍼센트로 변환
            "overdue_count": sum(1 for loan in self.loans.values() if any(
                (datetime.today() - datetime.strptime(payment.date, "%Y-%m-%d")).days > 30 
                for payment in loan.payments)),
            "total_late_fees": sum(LATE_FEE for loan in self.loans.values() 
                                   if any((datetime.today() - datetime.strptime(payment.date, "%Y-%m-%d")).days > 30 
                                          for payment in loan.payments))
        }
        return summary

# 예제 사용
loan_system = LoanSystem()
loan_system.create_loan(1, "Alice", 10000, 12)
loan_system.record_payment(1, 850, "2023-04-01")

monthly_report = loan_system.generate_monthly_report(2023, 4)
portfolio_summary = loan_system.summarize_portfolio()

print("Monthly Report:", monthly_report)
print("Portfolio Summary:", portfolio_summary)