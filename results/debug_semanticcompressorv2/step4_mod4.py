from typing import Optional, List, Dict

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
        self.budget_limits: Dict[str, float] = {}

    def add_transaction(self, tx_id: int, description: str, amount: float, date: str, category: str = "기타") -> None:
        if any(tx.tx_id == tx_id for tx in self.transactions):
            raise ValueError("Transaction ID already exists")
        
        if category in self.budget_limits and abs(amount) > self.budget_limits[category] - sum(tx.amount for tx in self.transactions if tx.category == category and not tx.cancelled):
            print(f"Warning: Adding this transaction will exceed the budget limit for category '{category}'.")
        
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

    def update_transaction(self, tx_id: int, **kwargs) -> None:
        tx = self.get_transaction(tx_id)
        if not tx:
            raise ValueError("Transaction not found")
        
        for key, value in kwargs.items():
            if hasattr(tx, key):
                setattr(tx, key, value)
            else:
                raise AttributeError(f"Invalid attribute: {key}")

    def get_all_transactions(self) -> List[Transaction]:
        return self.transactions

    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        return [tx for tx in self.get_all_transactions() if tx.category == category]

    def get_monthly_summary(self, year_month: str) -> Dict[str, float]:
        total = 0.0
        for tx in self.get_all_transactions():
            if tx.date.startswith(year_month):
                total += tx.amount
        return {"total": total}

    def set_budget_limit(self, category: str, limit: float) -> None:
        self.budget_limits[category] = limit

    def get_budget_status(self, category: str) -> Dict[str, float]:
        if category not in self.budget_limits:
            raise ValueError(f"No budget limit set for category '{category}'")
        
        used_amount = sum(tx.amount for tx in self.transactions if tx.category == category and not tx.cancelled)
        remaining_limit = max(0, self.budget_limits[category] - used_amount)
        return {
            "limit": self.budget_limits[category],
            "used": used_amount,
            "remaining": remaining_limit
        }

# Usage example:
tracker = BudgetTracker()
tracker.set_budget_limit("식비", 200.0)

tracker.add_transaction(1, "Groceries", 50.0, "2023-04-01", category="식비")
tracker.add_transaction(2, "Salary", 1000.0, "2023-04-01", category="수입")
tracker.add_transaction(3, "Groceries", -50.0, "2023-04-15", category="식비")  # Cancelled transaction

print("Budget Status for '식비':")
budget_status = tracker.get_budget_status("식비")
print(f"Limit: {budget_status['limit']}, Used: {budget_status['used']}, Remaining: {budget_status['remaining']}")

tracker.add_transaction(4, "Groceries", 100.0, "2023-04-20", category="식비")  # This should trigger a warning
print("\nAfter adding another transaction to '식비':")
budget_status = tracker.get_budget_status("식비")
print(f"Limit: {budget_status['limit']}, Used: {budget_status['used']}, Remaining: {budget_status['remaining']}")

tracker.cancel_transaction(1)
print("\nAfter cancelling transaction 1:")
for tx in tracker.get_all_transactions():
    print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")

print("\nTransactions by category '식비':")
for tx in tracker.get_transactions_by_category("식비"):
    print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")

# Monthly summary example
print("\nMonthly Summary for 2023-04:")
summary = tracker.get_monthly_summary("2023-04")
print(f"Total: {summary['total']}")

# Update transaction example:
tracker.update_transaction(2, description="Bonus", amount=1500.0)
print("\nAfter updating transaction 2:")
for tx in tracker.get_all_transactions():
    if tx.tx_id == 2:
        print(f"ID: {tx.tx_id}, Description: {tx.description}, Amount: {tx.amount}, Date: {tx.date}, Category: {tx.category}")