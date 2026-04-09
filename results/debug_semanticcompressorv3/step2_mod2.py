from typing import Dict, List, Optional

class Transaction:
    def __init__(self, tx_id: int, description: str, amount: float, date: str, category: str = "기타"):
        self.tx_id = tx_id
        self.description = description
        self.amount = amount
        self.date = date
        self.category = category
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

class BudgetTracker:
    def __init__(self):
        self.transactions: Dict[int, Transaction] = {}

    def add_transaction(self, tx_id: int, description: str, amount: float, date: str, category: str = "기타") -> None:
        if tx_id in self.transactions:
            raise ValueError("Transaction ID already exists")
        new_transaction = Transaction(tx_id, description, amount, date, category)
        self.transactions[tx_id] = new_transaction

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        return self.transactions.get(tx_id)

    def cancel_transaction(self, tx_id: int) -> None:
        if tx_id not in self.transactions:
            raise ValueError("Transaction ID does not exist")
        transaction_to_cancel = self.transactions[tx_id]
        if transaction_to_cancel.is_cancelled:
            raise ValueError("Transaction is already cancelled")
        cancellation_tx_id = f"{tx_id}_cancellation"
        new_cancellation_transaction = Transaction(cancellation_tx_id, "Cancellation", -transaction_to_cancel.amount, transaction_to_cancel.date, category="취소")
        self.transactions[cancellation_tx_id] = new_cancellation_transaction

    def get_all_transactions(self) -> List[Transaction]:
        return list(self.transactions.values())

    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        return [transaction for transaction in self.transactions.values() if transaction.category == category]

    def get_monthly_summary(self, year_month: str) -> float:
        month = int(year_month.split("-")[1])
        transactions_in_month = [
            transaction.amount
            for transaction in self.transactions.values()
            if transaction.date.startswith(f"{year_month}-") and not transaction.is_cancelled
        ]
        return sum(transactions_in_month)

# 간단한 사용 예제
budget_tracker = BudgetTracker()
budget_tracker.add_transaction(1, "Groceries", -20.50, "2023-10-01", "식비")
budget_tracker.add_transaction(2, "Salary", 3000.00, "2023-10-01", "수입")

print("All Transactions:")
for transaction in budget_tracker.get_all_transactions():
    print(f"ID: {transaction.tx_id}, Description: {transaction.description}, Amount: {transaction.amount}, Date: {transaction.date}, Category: {transaction.category}")

budget_tracker.cancel_transaction(1)
print("\nAfter cancelling Transaction ID 1:")

for transaction in budget_tracker.get_all_transactions():
    print(f"ID: {transaction.tx_id}, Description: {transaction.description}, Amount: {transaction.amount}, Date: {transaction.date}, Category: {transaction.category}")

print("\nTransactions by category '식비':")
for transaction in budget_tracker.get_transactions_by_category("식비"):
    print(f"ID: {transaction.tx_id}, Description: {transaction.description}, Amount: {transaction.amount}, Date: {transaction.date}, Category: {transaction.category}")

# Monthly summary
print("\nMonthly Summary for 2023-10:")
print(budget_tracker.get_monthly_summary("2023-10"))