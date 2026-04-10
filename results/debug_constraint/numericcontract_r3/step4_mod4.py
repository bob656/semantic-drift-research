from dataclasses import dataclass
from datetime import datetime, timedelta

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
    payments: list[Payment] = None

    def __post_init__(self):
        if self.payments is None:
            self.payments = []

class LoanSystem:
    def __init__(self):
        self.loans = {}
        self.next_payment_id = 1

    def create_loan(self, loan_id: int, borrower: str, principal: float, months: int) -> bool:
        if months > MAX_INSTALLMENTS:
            return False
        new_loan = Loan(loan_id, borrower, principal, months, "active")
        self.loans[loan_id] = new_loan
        return True

    def calculate_monthly_payment(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        return max(monthly_payment, MIN_PAYMENT)

    def apply_late_fee(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        penalty_amount = LATE_FEE + (loan.principal * PENALTY_RATE)
        loan.principal += penalty_amount

    def get_loan(self, loan_id: int) -> Loan:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        return self.loans[loan_id]

    def record_payment(self, loan_id: int, amount: float, date: str, payment_type='REGULAR'):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        payment = Payment(payment_id=self.next_payment_id, loan_id=loan_id, amount=amount, date=date, type=payment_type)
        loan.payments.append(payment)
        self.next_payment_id += 1

    def get_payment_history(self, loan_id: int) -> list[Payment]:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        return loan.payments

    def calculate_early_repayment_discount(self, remaining_balance, remaining_months):
        remaining_interest = remaining_balance * (INTEREST_RATE / 12) * remaining_months
        discount = remaining_interest * 0.1
        return discount

    def get_payoff_amount(self, loan_id):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        total_paid = sum(payment.amount for payment in loan.payments)
        remaining_balance = loan.principal - total_paid
        return remaining_balance

    def check_overdue(self, loan_id: int, last_payment_date: str, today: str) -> bool:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        # Convert string dates to datetime objects
        last_payment = datetime.strptime(last_payment_date, "%Y-%m-%d")
        current_day = datetime.strptime(today, "%Y-%m-%d")
        
        # Check if more than 30 days have passed since the last payment
        return (current_day - last_payment).days > 30

    def get_overdue_amount(self, loan_id: int) -> float:
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        overdue_amount = 0.0
        
        # Assuming the last payment date is the latest payment's date
        if loan.payments:
            last_payment_date = loan.payments[-1].date
            today = datetime.now().strftime("%Y-%m-%d")
            
            if self.check_overdue(loan_id, last_payment_date, today):
                overdue_days = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(last_payment_date, "%Y-%m-%d")).days
                penalty_interest_rate = INTEREST_RATE + PENALTY_RATE
                
                # Calculate the overdue amount
                remaining_balance = sum(payment.amount for payment in loan.payments)
                overdue_amount += remaining_balance * (1 + penalty_interest_rate) ** (overdue_days / 30)
                overdue_amount += LATE_FEE
        
        return overdue_amount

    def generate_payment_schedule(self, loan_id: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        principal_remaining = loan.principal
        schedule = []

        for i in range(1, loan.months + 1):
            interest = principal_remaining * r
            if monthly_payment < interest:
                raise ValueError("Monthly payment is less than the interest.")
            principal_paid = monthly_payment - interest
            principal_remaining -= principal_paid

            schedule.append({
                "installment_number": i,
                "payment_amount": round(monthly_payment, 2),
                "principal_part": round(principal_paid, 2),
                "interest_part": round(interest, 2),
                "balance": round(principal_remaining, 2)
            })

        return schedule

    def get_remaining_balance(self, loan_id: int, paid_months: int):
        if loan_id not in self.loans:
            raise ValueError("Loan ID does not exist.")
        
        if paid_months < 0 or paid_months > MAX_INSTALLMENTS:
            raise ValueError("Invalid number of paid months.")
        
        loan = self.loans[loan_id]
        r = INTEREST_RATE / 12
        monthly_payment = (loan.principal * r) / (1 - (1 + r) ** (-loan.months))
        principal_remaining = loan.principal

        for _ in range(paid_months):
            interest = principal_remaining * r
            principal_paid = monthly_payment - interest
            principal_remaining -= principal_paid

        return round(principal_remaining, 2)

# Example usage
loan_system = LoanSystem()
loan_created = loan_system.create_loan(1, "John Doe", 5000000.0, 36)
if loan_created:
    monthly_payment = loan_system.calculate_monthly_payment(1)
    print(f"Monthly payment: {monthly_payment}")

    # Simulate a late fee
    loan_system.apply_late_fee(1)
    updated_loan = loan_system.get_loan(1)
    print(f"Updated principal after late fee: {updated_loan.principal}")

    # Record payments
    loan_system.record_payment(1, 200000, "2023-10-01")
    loan_system.record_payment(1, 250000, "2023-11-01", payment_type='EARLY')

    # Get payment history
    payment_history = loan_system.get_payment_history(1)
    for payment in payment_history:
        print(f"Payment ID: {payment.payment_id}, Date: {payment.date}, Amount: {payment.amount}, Type: {payment.type}")

    # Calculate early repayment discount and payoff amount
    remaining_months = 34  # Assuming 2 months have already been paid
    remaining_balance = loan_system.get_payoff_amount(1)
    discount = loan_system.calculate_early_repayment_discount(remaining_balance, remaining_months)
    print(f"Early Repayment Discount: {discount}")
    print(f"Payoff Amount: {remaining_balance - discount}")

    # Check overdue and get overdue amount
    last_payment_date = "2023-10-01"
    today = datetime.now().strftime("%Y-%m-%d")
    is_overdue = loan_system.check_overdue(1, last_payment_date, today)
    print(f"Is the loan overdue? {is_overdue}")
    if is_overdue:
        overdue_amount = loan_system.get_overdue_amount(1)
        print(f"Overdue amount: {overdue_amount}")

    # Generate payment schedule and get remaining balance
    payment_schedule = loan_system.generate_payment_schedule(1)
    for entry in payment_schedule[:5]:  # Display first 5 installments
        print(entry)

    remaining_balance_after_2_months = loan_system.get_remaining_balance(1, 2)
    print(f"Remaining balance after 2 months: {remaining_balance_after_2_months}")

else:
    print("Loan creation failed due to invalid months.")