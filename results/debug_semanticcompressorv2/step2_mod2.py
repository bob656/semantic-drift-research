from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.calculate_total()

    def calculate_total(self) -> None:
        total_before_discount = sum(item.price * item.quantity for item in self.items)
        self.total = total_before_discount * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        new_order = Order(order_id, items, discount_percent)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        del self.orders[order_id]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].calculate_total()

    def get_order_total(self, order_id: int) -> float:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        return self.orders[order_id].total

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
order_manager = OrderManager()

item1 = Item(name="Apple", price=0.5, quantity=2)
item2 = Item(name="Banana", price=0.3, quantity=3)

order_manager.add_order(1, [item1, item2], discount_percent=0.1)  # 10% 할인

item3 = Item(name="Orange", price=0.7, quantity=1)

order_manager.add_order(2, [item3], discount_percent=0.2)  # 20% 할인

print(order_manager.get_order(1))  # Order object with order_id 1 and discounted total
print(f"Order 1 Total: {order_manager.get_order_total(1)}")  # Discounted total of Order 1

order_manager.apply_discount(1, discount_percent=0.15)  # Additional 15% discount on Order 1

print(order_manager.get_order(1))  # Updated Order object with order_id 1 and new discounted total
print(f"Order 1 Total: {order_manager.get_order_total(1)}")  # New discounted total of Order 1

order_manager.cancel_order(1)

print(order_manager.list_orders())  # List of all orders except the canceled one