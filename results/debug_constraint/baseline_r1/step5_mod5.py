from dataclasses import dataclass
import datetime

# 핵심 수치 상수
INTEREST_RATE = 0.025
LATE_FEE = 5000
MAX_INSTALLMENTS = 36
MIN_PAYMENT = 10000
PENALTY_RATE = 0.015
OVERDUE_DAYS_THRESHOLD = 30

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

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}

    # 기존 메서드들...

    def generate_monthly_report(self, year, month):
        """해당 월 대출 현황 딕셔너리 반환"""
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }
        
        for loan in self.loans.values():
            if int(loan.date.split('-')[1]) == month and int(loan.date.split('-')[0]) == year:
                report["total_loans"] += 1
                report["total_principal"] += loan.principal
                if self.check_overdue(loan.loan_id, last_payment_date=self.get_last_payment_date(loan.loan_id), today=datetime.datetime.now().strftime('%Y-%m-%d')):
                    report["overdue_count"] += 1
                    report["total_late_fees"] += LATE_FEE

        if report["total_loans"] > 0:
            report["average_rate"] = INTEREST_RATE / 12 * 100  # 이율을 퍼센트로 변환

        return report

    def summarize_portfolio(self):
        """전체 포트폴리오 요약 반환"""
        summary = {
            "total_loans": len(self.loans),
            "total_principal": sum(loan.principal for loan in self.loans.values()),
            "average_rate": INTEREST_RATE / 12 * 100,  # 이율을 퍼센트로 변환
            "overdue_count": sum(1 for loan in self.loans.values() if self.check_overdue(loan.loan_id, last_payment_date=self.get_last_payment_date(loan.loan_id), today=datetime.datetime.now().strftime('%Y-%m-%d'))),
            "total_late_fees": sum(LATE_FEE for loan in self.loans.values() if self.check_overdue(loan.loan_id, last_payment_date=self.get_last_payment_date(loan.loan_id), today=datetime.datetime.now().strftime('%Y-%m-%d')))
        }
        
        return summary

    def get_last_payment_date(self, loan_id):
        """대출의 마지막 납부일 반환"""
        if loan_id in self.payment_history and self.payment_history[loan_id]:
            return max(payment.date for payment in self.payment_history[loan_id])
        else:
            return "2023-01-01"