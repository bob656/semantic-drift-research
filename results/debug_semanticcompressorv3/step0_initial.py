from typing import Dict, List, Optional

class Transaction:
    def __init__(self, tx_id: int, description: str, amount: float, date: str):
        self.tx_id = tx_id
        self.description = description
        self.amount = amount
        self.date = date
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

class BudgetTracker:
    def __init__(self):
        self.transactions: Dict[int, Transaction] = {}

    def add_transaction(self, tx_id: int, description: str, amount: float, date: str) -> None:
        if tx_id in self.transactions:
            raise ValueError("Transaction ID already exists")
        new_transaction = Transaction(tx_id, description, amount, date)
        self.transactions[tx_id] = new_transaction

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        return self.transactions.get(tx_id)

    def cancel_transaction(self, tx_id: int) -> None:
        if tx_id not in self.transactions:
            raise ValueError("Transaction ID does not exist")
        transaction_to_cancel = self.transactions[tx_id]
        if transaction_to_cancel.is_cancelled:
            raise ValueError("Transaction is already cancelled")
        cancellation_tx_id = tx_id * -1  # Using negative IDs for cancellations
        new_cancellation_transaction = Transaction(cancellation_tx_id, f"Cancel {transaction_to_cancel.description}", -transaction_to_cancel.amount, transaction_to_cancel.date)
        self.transactions[cancellation_tx_id] = new_cancellation_transaction

    def get_all_transactions(self) -> List[Transaction]:
        return list(self.transactions.values())

# 간단한 사용 예제
budget_tracker = BudgetTracker()
budget_tracker.add_transaction(1, "Groceries", -20.50, "2023-10-01")
budget_tracker.add_transaction(2, "Salary", 3000.00, "2023-10-01")

print("All Transactions:")
for transaction in budget_tracker.get_all_transactions():
    print(f"ID: {transaction.tx_id}, Description: {transaction.description}, Amount: {transaction.amount}, Date: {transaction.date}")

budget_tracker.cancel_transaction(1)
print("\nAfter cancelling Transaction ID 1:")

for transaction in budget_tracker.get_all_transactions():
    print(f"ID: {transaction.tx_id}, Description: {transaction.description}, Amount: {transaction.amount}, Date: {transaction.date}")