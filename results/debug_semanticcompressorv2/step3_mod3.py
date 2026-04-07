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
        self.status = "PENDING"

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
        """주문을 취소합니다(상태만 변경)."""
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"
        else:
            raise ValueError(f"주문 상태 {order.status}에서는 취소가 불가능합니다")

    def confirm_order(self, order_id: int) -> None:
        """주문을 확인합니다(PENDING → CONFIRMED)."""
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist.")
        order = self.orders[order_id]
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError(f"주문 상태 {order.status}에서는 확인이 불가능합니다")

    def ship_order(self, order_id: int) -> None:
        """주문을 배송합니다(CONFIRMED → SHIPPED)."""
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist.")
        order = self.orders[order_id]
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError(f"주문 상태 {order.status}에서는 배송이 불가능합니다")

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
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 주문 확인
    try:
        manager.confirm_order(1)
    except ValueError as e:
        print(e)

    # 주문 배송
    try:
        manager.ship_order(1)
    except ValueError as e:
        print(e)

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 할인된 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total after discount: {order.total}, Status: {order.status}")

    # 주문 취소 (try/except로 감싸야 함)
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 취소된 후 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")