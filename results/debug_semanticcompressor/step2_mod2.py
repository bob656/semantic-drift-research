from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = max(0.0, min(1.0, discount_percent))  # Ensure within range [0.0, 1.0]
        self.total = sum(item.price * item.quantity for item in items) * (1 - self.discount_percent)

    def apply_discount(self, discount_percent: float):
        self.discount_percent = max(0.0, min(1.0, discount_percent))  # Ensure within range [0.0, 1.0]
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문 목록을 저장할 딕셔너리 초기화
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        # 새로운 주문 추가
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items, discount_percent)
            print(f"Order with ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        # 주문 취소 (삭제)
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order with ID {order_id} has been cancelled.")
        else:
            print(f"No order found with ID {order_id}.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        # 주문에 할인 적용
        order = self.get_order(order_id)
        if order:
            order.apply_discount(discount_percent)
            print(f"Discount applied to Order ID {order_id}.")
        else:
            print(f"No order found with ID {order_id}.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        # 주문의 최종 금액 반환
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}.")
            return None

    def list_orders(self) -> List[Order]:
        # 모든 주문 목록 반환 (할인 적용 후 total 포함)
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    manager.add_order(1, [Item("apple", 0.99, 2), Item("banana", 0.59, 3)], discount_percent=0.1)
    manager.add_order(2, [Item("orange", 1.49, 1)])

    print("Order 1:", [item.name for item in manager.get_order(1).items])  # ['apple', 'banana']
    print("Order 1 Total after discount:", manager.get_order_total(1))  # Should be less than original total

    manager.apply_discount(1, 0.2)
    print("Order 1 Total after additional 20% discount:", manager.get_order_total(1))

    print("List of orders with discounts applied:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}")

    manager.cancel_order(1)
    print("List of orders after cancelling order 1:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}")