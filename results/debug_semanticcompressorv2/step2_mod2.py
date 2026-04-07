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
        self.discount_percent = discount_percent
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        """할인을 적용한 총 가격 계산"""
        total = sum(item.price * item.quantity for item in self.items)
        return total * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        """주문을 조회합니다. 주문이 없으면 None을 반환합니다."""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """주문을 취소합니다(삭제합니다)."""
        if order_id in self.orders:
            del self.orders[order_id]
        else:
            raise ValueError(f"Order ID {order_id} does not exist.")

    def list_orders(self) -> List[Order]:
        """모든 주문 목록을 반환합니다."""
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인율 적용"""
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist.")
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """주문의 최종 금액 반환"""
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order ID {order_id} does not exist.")
        return order.total

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()

    # 주문 추가
    items1 = [Item("item1", 5.25, 2), Item("item2", 3.75, 1)]
    manager.add_order(1, items1)
    items2 = [Item("item3", 4.00, 1)]
    manager.add_order(2, items2)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}")

    # 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}")

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 할인된 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total after discount: {order.total}")

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}")