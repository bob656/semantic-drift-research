from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

    def apply_discount(self, discount_percent: float):
        if 0 <= discount_percent <= 1:
            self.discount_percent = discount_percent
            self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)
        else:
            raise ValueError("discount percent must be between 0.0 and 1.0")

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> bool:
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items, discount_percent)
            return True
        return False

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def apply_discount(self, order_id: int, discount_percent: float):
        if order_id in self.orders:
            self.orders[order_id].apply_discount(discount_percent)
        else:
            raise KeyError("Order not found")

    def get_order_total(self, order_id: int) -> Optional[float]:
        return self.orders.get(order_id)?.total

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values()]

# 간단한 사용 예제
order_manager = OrderManager()
order_manager.add_order(1, [Item("apple", 0.5), Item("banana", 0.3)], discount_percent=0.1)
order_manager.add_order(2, [Item("steak", 10.0), Item("potatoes", 1.5)])

print(order_manager.get_order(1))
print(order_manager.list_orders())

order_manager.apply_discount(1, discount_percent=0.2)
print(order_manager.get_order_total(1))
print(order_manager.list_orders())