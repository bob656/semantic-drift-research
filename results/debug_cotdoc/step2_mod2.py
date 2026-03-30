from dataclasses import dataclass
from typing import List, Optional, Dict

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
        self.total = sum(item.price * item.quantity for item in items) * (1 - self.discount_percent)


class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}

    def add_order(self, order_id: int, items: List[Item]):
        if order_id in self.orders:
            raise ValueError("Order ID already exists.")
        if not isinstance(order_id, int):
            raise TypeError("order_id must be an integer.")
        if not isinstance(items, list):
            raise TypeError("items must be a list.")
        for item in items:
            if not isinstance(item, Item):
                raise TypeError("items must be a list of Item objects.")
            if not isinstance(item.price, float):
                raise TypeError("Item price must be a float.")
            if not isinstance(item.quantity, int):
                raise TypeError("Item quantity must be an integer.")
            if item.price < 0 or item.quantity < 0:
                raise ValueError("Item price and quantity cannot be negative.")

        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0.")
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = sum(item.price * item.quantity for item in order.items) * (1 - order.discount_percent)

    def get_order_total(self, order_id: int) -> float:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0


# 사용 예제
order_manager = OrderManager()

# 주문 추가
try:
    order_manager.add_order(1, [Item("apple", 1.0, 2), Item("banana", 0.5, 4)])
    order_manager.add_order(2, [Item("orange", 0.75, 8)])
except ValueError as e:
    print(f"Error: {e}")
except TypeError as e:
    print(f"Error: {e}")


# 주문 조회
order1 = order_manager.get_order(1)
if order1:
    print(f"Order 1: ID={order1.order_id}, Items={order1.items}, Total={order1.total}")
else:
    print("Order 1 not found.")

# 할인 적용
order_manager.apply_discount(1, 0.1)

# 주문 총액 조회
total1 = order_manager.get_order_total(1)
print(f"Order 1 Total: {total1}")

# 모든 주문 목록 조회
all_orders = order_manager.list_orders()
print("All Orders:")
for order in all_orders:
    print(f"  ID={order.order_id}, Items={[item.name for item in order.items]}, Total={order.total}")

# 예외 처리 테스트
try:
    order_manager.add_order(1, [Item("apple", 1.0, -2)])
except ValueError as e:
    print(f"Error: {e}")

try:
    order_manager.add_order("a", [Item("apple", 1.0, 2)])
except TypeError as e:
    print(f"Error: {e}")

try:
    order_manager.apply_discount(1, 1.2)
except ValueError as e:
    print(f"Error: {e}")