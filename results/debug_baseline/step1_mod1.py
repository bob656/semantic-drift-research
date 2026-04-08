from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> bool:
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items)
            return True
        return False

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
order_manager = OrderManager()
order_manager.add_order(1, [Item("apple", 0.5), Item("banana", 0.3)])
order_manager.add_order(2, [Item("steak", 10.0), Item("potatoes", 1.5)])

print(order_manager.get_order(1))
print(order_manager.list_orders())

order_manager.cancel_order(1)
print(order_manager.list_orders())