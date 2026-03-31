from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.discount_percent: float = 0.0  # 할인율 필드 추가
        self.total = self.calculate_total()

    def __repr__(self):
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total})"

    def calculate_total(self) -> float:
        total = 0.0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)


class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}  # order_id를 키로 사용

    def add_order(self, order_id: int, items: List[Item]) -> None:
        """주문 추가. order_id 중복 검사 수행."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        """주문 ID에 해당하는 주문 조회. 주문이 없으면 None 반환."""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """주문 ID에 해당하는 주문 취소 (삭제). 주문이 없으면 아무런 동작을 하지 않음."""
        if order_id in self.orders:
            del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        """모든 주문 목록 반환."""
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인율 적용."""
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """주문 ID에 해당하는 주문의 최종 금액 반환."""
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0


# 사용 예제
if __name__ == "__main__":
    # OrderManager 인스턴스 생성
    order_manager = OrderManager()

    # 주문 추가
    try:
        order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 20.0, 1)])
        order_manager.add_order(2, [Item("item3", 5.0, 10)])
    except ValueError as e:
        print(f"Error adding order: {e}")
        exit()

    # 주문 조회
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    # 주문 목록 확인
    orders = order_manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Total: {order.total}")

    # 주문 취소
    order_manager.cancel_order(1)

    # 취소된 주문 조회 (None 반환)
    order = order_manager.get_order(1)
    print(f"Order ID 1 exists: {order is None}")

    # 할인 적용
    order_manager.apply_discount(2, 0.1)  # 10% 할인
    order = order_manager.get_order(2)
    if order:
        print(f"Order ID: {order.order_id}, Discount Percent: {order.discount_percent}, Total: {order.total}")

    # 총액 조회
    total = order_manager.get_order_total(2)
    print(f"Order 2 total: {total}")