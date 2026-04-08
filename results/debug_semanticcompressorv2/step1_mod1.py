from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        new_order = Order(order_id, items)
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

item1 = Item(name="Apple", price=0.5, quantity=2)
item2 = Item(name="Banana", price=0.3, quantity=3)

order_manager.add_order(1, [item1, item2])

item3 = Item(name="Orange", price=0.7, quantity=1)

order_manager.add_order(2, [item3])

print(order_manager.get_order(1))  # Order object with order_id 1

order_manager.cancel_order(1)

print(order_manager.list_orders())  # List of all orders except the canceled one