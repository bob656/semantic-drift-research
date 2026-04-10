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

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.payment_history = {}

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans[loan_id] = new_loan
        self.payment_history[loan_id] = []
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        late_fee = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += late_fee

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan does not exist.")
        
        payment = Payment(payment_id=len(self.payment_history[loan_id]) + 1,
                          loan_id=loan_id,
                          amount=amount,
                          date=date,
                          type=payment_type)
        
        self.payment_history[loan_id].append(payment)

    def get_payment_history(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan does not exist.")
        
        return self.payment_history.get(loan_id, [])

    def get_loan(self, loan_id: int) -> Loan:
        return self.loans.get(loan_id)

    def calculate_early_repayment(self, loan_id: int, remaining_balance: float):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        r = INTEREST_RATE / 12
        remaining_months = loan.months - len(self.payment_history[loan_id])
        remaining_interest = remaining_balance * r * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        remaining_payments = len(self.payment_history[loan_id])
        total_paid = sum(payment.amount for payment in self.payment_history[loan_id])
        payoff_amount = loan.principal - total_paid
        return payoff_amount

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        last_payment_date = datetime.strptime(last_payment_date, "%Y-%m-%d")
        today_date = datetime.strptime(today, "%Y-%m-%d")
        delta = today_date - last_payment_date
        return delta.days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        overdue_amount = 0
        for payment in self.payment_history[loan_id]:
            if payment.type == 'REGULAR':
                overdue_amount += MIN_PAYMENT
        overdue_amount += LATE_FEE + (loan.principal * PENALTY_RATE)
        return overdue_amount

    def generate_payment_schedule(self, loan_id: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        balance = loan.principal
        
        schedule = []
        for month in range(1, loan.months + 1):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
            
            schedule.append({
                "month": month,
                "payment": monthly_payment,
                "principal": principal_paid,
                "interest": interest,
                "balance": balance
            })
        
        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        loan = self.loans.get(loan_id)
        if not loan or loan.status != "active":
            raise ValueError("Loan is either non-existent or inactive.")
        
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        balance = loan.principal
        
        for _ in range(paid_months):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
        
        return balance

    def generate_monthly_report(self, year: int, month: int):
        report = {
            "total_loans": 0,
            "total_principal": 0.0,
            "average_rate": 0.0,
            "overdue_count": 0,
            "total_late_fees": 0.0
        }
        
        for loan_id, loan in self.loans.items():
            if loan.status != "active":
                continue
            
            report["total_loans"] += 1
            report["total_principal"] += loan.principal
            
            # Calculate overdue count and total late fees
            last_payment_date = datetime.strptime(max(payment.date for payment in self.payment_history[loan_id]), "%Y-%m-%d")
            today = datetime(year, month, 1)
            if (today - last_payment_date).days > 30:
                report["overdue_count"] += 1
                report["total_late_fees"] += LATE_FEE + (loan.principal * PENALTY_RATE)
        
        # Calculate average rate
        if report["total_loans"] > 0:
            report["average_rate"] = INTEREST_RATE
        
        return report

    def summarize_portfolio(self):
        summary = {
            "active_loans": 0,
            "inactive_loans": 0,
            "total_principal": 0.0,
            "total_late_fees": 0.0,
            "overdue_count": 0
        }
        
        for loan_id, loan in self.loans.items():
            if loan.status == "active":
                summary["active_loans"] += 1
                summary["total_principal"] += loan.principal
                
                # Calculate overdue count and total late fees
                last_payment_date = datetime.strptime(max(payment.date for payment in self.payment_history[loan_id]), "%Y-%m-%d")
                today = datetime.now()
                if (today - last_payment_date).days > 30:
                    summary["overdue_count"] += 1
                    summary["total_late_fees"] += LATE_FEE + (loan.principal * PENALTY_RATE)
            else:
                summary["inactive_loans"] += 1
        
        return summary

# Example usage
if __name__ == "__main__":
    system = LoanSystem()
    
    # Create a loan
    created = system.create_loan(1, "Alice", 500000, 36)
    print(f"Loan created: {created}")
    
    # Calculate monthly payment
    try:
        payment = system.calculate_monthly_payment(1)
        print(f"Monthly payment: {payment:.2f}원")
    except ValueError as e:
        print(e)
    
    # Apply late fee
    system.apply_late_fee(1)
    loan = system.get_loan(1)
    print(f"Loan principal after late fee: {loan.principal:.2f}원")

    # Record a payment
    system.record_payment(1, 30000, "2024-01-15", 'REGULAR')
    payment_history = system.get_payment_history(1)
    print(f"Payment history for loan ID 1: {payment_history}")

    # Calculate early repayment discount and payoff amount
    try:
        remaining_balance = 300000  # Example remaining balance
        discount = system.calculate_early_repayment(1, remaining_balance)
        payoff_amount = system.get_payoff_amount(1)
        print(f"Early repayment discount: {discount:.2f}원")
        print(f"Payoff amount: {payoff_amount:.2f}원")
    except ValueError as e:
        print(e)

    # Check overdue and get overdue amount
    try:
        is_overdue = system.check_overdue(1, "2024-01-01", "2024-03-15")
        print(f"Is loan 1 overdue? {is_overdue}")
        overdue_amount = system.get_overdue_amount(1)
        print(f"Overdue amount for loan 1: {overdue_amount:.2f}원")
    except ValueError as e:
        print(e)

    # Generate monthly report
    try:
        report = system.generate_monthly_report(2024, 3)
        print("Monthly Report:")
        print(report)
    except Exception as e:
        print(f"Error generating monthly report: {e}")

    # Summarize portfolio
    try:
        summary = system.summarize_portfolio()
        print("Portfolio Summary:")
        print(summary)
    except Exception as e:
        print(f"Error summarizing portfolio: {e}")