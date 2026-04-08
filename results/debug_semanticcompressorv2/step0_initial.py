from typing import List, Optional

class Order:
    def __init__(self, order_id: int, items: List[str], total: float):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[str], total: float) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        new_order = Order(order_id, items, total)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
order_manager = OrderManager()
order_manager.add_order(1, ["Apple", "Banana"], 2.5)
order_manager.add_order(2, ["Orange"], 1.0)

print(order_manager.get_order(1))  # Order object with order_id 1

order_manager.cancel_order(1)

print(order_manager.list_orders())  # List of all orders except the canceled one