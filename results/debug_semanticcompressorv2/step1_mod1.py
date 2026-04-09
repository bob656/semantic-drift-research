from typing import Optional, List

class Transaction:
    def __init__(self, tx_id: int, description: str, amount: float, date: str, category: str = "기타"):
        self.tx_id = tx_id
        self.description = description
        self.amount = amount
        self.date = date
        self.category = category
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

class BudgetTracker:
    def __init__(self):
        self.transactions: List[Transaction] = []

    def add_transaction(self, tx_id: int, description: str, amount: float, date: str, category: str = "기타") -> None:
        if any(tx.tx_id == tx_id for tx in self.transactions):
            raise ValueError("Transaction ID already exists")
        new_tx = Transaction(tx_id, description, amount, date, category)
        self.transactions.append(new_tx)

    def get_transaction(self, tx_id: int) -> Optional[Transaction]:
        return next((tx for tx in self.transactions if tx.tx_id == tx_id), None)

    def cancel_transaction(self, tx_id: int) -> None:
        tx = self.get_transaction(tx_id)
        if not tx:
            raise ValueError("Transaction not found")
        if tx.cancelled:
            raise ValueError("Transaction already cancelled")

        new_tx = Transaction(tx_id, tx.description, -tx.amount, tx.date, tx.category)  # Cancel by adding a negative transaction
        new_tx.cancel()
        self.transactions.append(new_tx)

    def get_all_transactions(self) -> List[Transaction]:
        return self.transactions

    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        return [tx for tx in self.transactions if tx.category == category]

# Usage example:
tracker = BudgetTracker()
tracker.add_transaction(1, "Groceries", 50.0, "2023-04-01", category="식비")
tracker.add_transaction(2, "Salary", 1000.0, "2023-04-01", category="수입")

print("All Transactions:")
for tx in tracker.get_all_transactions():
    print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")

tracker.cancel_transaction(1)
print("\nAfter cancelling transaction 1:")
for tx in tracker.get_all_transactions():
    print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")

print("\nTransactions by category '식비':")
for tx in tracker.get_transactions_by_category("식비"):
    print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")