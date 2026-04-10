from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

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
    payments: Dict[int, Payment] = None  # 추가된 부분

class LoanSystem:
    def __init__(self):
        self.loans: Dict[int, Loan] = {}
        self.payment_id_counter = 1  # 추가된 부분

    # 기존 메서드들...

    def generate_payment_schedule(self, loan_id: int) -> Optional[Dict[int, dict]]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        schedule = {}
        remaining_principal = loan.principal
        r = INTEREST_RATE / 12
        for i in range(1, loan.months + 1):
            interest = remaining_principal * r
            principal_payment = self.calculate_monthly_payment(loan_id) - interest
            remaining_principal -= principal_payment
            schedule[i] = {
                'installment': i,
                'payment_amount': self.calculate_monthly_payment(loan_id),
                'principal_payment': principal_payment,
                'interest_payment': interest,
                'balance': remaining_principal
            }
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int) -> Optional[float]:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != 'active':
            return None
        remaining_principal = loan.principal
        r = INTEREST_RATE / 12
        for i in range(1, min(paid_months + 1, loan.months + 1)):
            interest = remaining_principal * r
            principal_payment = self.calculate_monthly_payment(loan_id) - interest
            remaining_principal -= principal_payment
        return max(remaining_principal, 0)

    def generate_monthly_report(self, year: int, month: int) -> Dict[str, float]:
        report = {
            'total_loans': 0,
            'total_principal': 0.0,
            'average_rate': 0.0,
            'overdue_count': 0,
            'total_late_fees': 0.0
        }
        
        for loan in self.loans.values():
            if loan.status == 'active':
                report['total_loans'] += 1
                report['total_principal'] += loan.principal
                
                # Calculate average rate (assuming all loans have the same interest rate)
                report['average_rate'] = INTEREST_RATE

                # Check for overdue payments
                current_date = datetime.now()
                for payment in loan.payments.values():
                    if payment.type == 'LATE':
                        payment_date = datetime.strptime(payment.date, '%Y-%m-%d')
                        if (current_date.year == year and current_date.month == month) or \
                           (payment_date.year < year or (payment_date.year == year and payment_date.month < month)):
                            report['overdue_count'] += 1
                            report['total_late_fees'] += LATE_FEE
        
        return report

    def summarize_portfolio(self) -> Dict[str, float]:
        summary = {
            'total_loans': len(self.loans),
            'total_principal': sum(loan.principal for loan in self.loans.values() if loan.status == 'active'),
            'average_rate': INTEREST_RATE,
            'overdue_count': sum(len([p for p in loan.payments.values() if p.type == 'LATE']) for loan in self.loans.values() if loan.status == 'active'),
            'total_late_fees': sum(LATE_FEE * len([p for p in loan.payments.values() if p.type == 'LATE']) for loan in self.loans.values() if loan.status == 'active')
        }
        
        return summary

# Example usage:
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 500000, 36)
if loan_created:
    print("Loan created successfully.")
else:
    print("Failed to create loan due to invalid term.")

monthly_payment = loan_system.calculate_monthly_payment(1)
if monthly_payment is not None:
    print(f"Monthly payment: {monthly_payment}원")
else:
    print("Failed to calculate monthly payment or loan does not exist.")

loan_system.record_payment(1, 20000, "2023-10-01", "REGULAR")

payment_history = loan_system.get_payment_history(1)
if payment_history is not None:
    for payment in payment_history.values():
        print(f"Payment ID: {payment.payment_id}, Amount: {payment.amount}원, Date: {payment.date}, Type: {payment.type}")
else:
    print("No payment history found.")

loan_system.apply_late_fee(1)

early_repayment_discount = loan_system.calculate_early_repayment(1, 400000, 30)
if early_repayment_discount is not None:
    print(f"Early repayment discount: {early_repayment_discount}원")
else:
    print("Failed to calculate early repayment discount or loan does not exist.")

payoff_amount = loan_system.get_payoff_amount(1)
if payoff_amount is not None:
    print(f"Payoff amount: {payoff_amount}원")
else:
    print("Failed to get payoff amount or loan does not exist.")

loan = loan_system.get_loan(1)
if loan:
    print(f"Loan details: ID={loan.loan_id}, Borrower={loan.borrower}, Principal={loan.principal}원, Months={loan.months}")
else:
    print("Loan not found.")

# Generate and print monthly report for January 2023
monthly_report = loan_system.generate_monthly_report(2023, 1)
print(f"Monthly Report (January 2023): {monthly_report}")

# Summarize portfolio
portfolio_summary = loan_system.summarize_portfolio()
print(f"Portfolio Summary: {portfolio_summary}")