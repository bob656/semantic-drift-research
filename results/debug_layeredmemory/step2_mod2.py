from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    """주문 품목을 나타내는 클래스."""
    name: str
    price: float
    quantity: int


class Order:
    """주문을 나타내는 클래스."""

    def __init__(self, order_id: int, items: List[Item]):
        """
        Order 객체를 초기화합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
        """
        self.order_id = order_id
        self.items = items
        self.discount_percent = 0.0  # 할인율을 추가합니다.
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        """주문 총액을 계산합니다."""
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)

    def __repr__(self):
        """Order 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, discount_percent={self.discount_percent}, total={self.total})"


class OrderManager:
    """주문 관리 기능을 제공하는 클래스."""

    def __init__(self):
        """OrderManager 객체를 초기화합니다."""
        self.orders: dict[int, Order] = {}  # 주문 ID를 키로 사용하여 주문을 저장합니다.

    def add_order(self, order_id: int, items: List[Item]) -> Order:
        """주문을 추가합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.

        Returns:
            추가된 Order 객체.
        """
        order = Order(order_id, items)
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        """주문 ID로 주문을 조회합니다.

        Args:
            order_id: 조회할 주문 ID.

        Returns:
            주문이 있으면 Order 객체를 반환하고, 없으면 None을 반환합니다.
        """
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> bool:
        """주문을 취소합니다(삭제).

        Args:
            order_id: 취소할 주문 ID.

        Returns:
            주문이 성공적으로 취소되면 True를 반환하고, 없으면 False를 반환합니다.
        """
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        else:
            return False

    def list_orders(self) -> List[Order]:
        """모든 주문 목록을 반환합니다.

        Returns:
            Order 객체의 목록.
        """
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인을 적용합니다.

        Args:
            order_id: 할인을 적용할 주문 ID.
            discount_percent: 적용할 할인율 (0.0 ~ 1.0).
        """
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> Optional[float]:
        """주문 총액을 반환합니다.

        Args:
            order_id: 주문 ID.

        Returns:
            주문 총액. 주문이 없으면 None.
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    order1 = order_manager.add_order(1, [Item("Laptop", 1200.00, 1), Item("Mouse", 25.00, 1)])
    order2 = order_manager.add_order(2, [Item("Keyboard", 75.00, 1), Item("Monitor", 300.00, 1)])

    # 주문 조회
    found_order = order_manager.get_order(1)
    if found_order:
        print(f"주문 ID 1에 대한 주문: {found_order}")
    else:
        print("주문 ID 1에 대한 주문을 찾을 수 없습니다.")

    # 주문 목록
    all_orders = order_manager.list_orders()
    print("모든 주문:")
    for order in all_orders:
        print(order)

    # 할인 적용
    order_manager.apply_discount(1, 0.1)  # 10% 할인

    # 주문 목록(할인 적용 후)
    all_orders = order_manager.list_orders()
    print("할인 적용 후의 모든 주문:")
    for order in all_orders:
        print(order)

    # 주문 취소
    order_manager.cancel_order(2)

    # 주문 목록(취소 후)
    all_orders = order_manager.list_orders()
    print("취소 후의 모든 주문:")
    for order in all_orders:
        print(order)

    # 존재하지 않는 주문 조회
    not_found_order = order_manager.get_order(3)
    if not_found_order is None:
        print("주문 ID 3에 대한 주문을 찾을 수 없습니다.")

    # 주문 총액 조회
    total = order_manager.get_order_total(1)
    if total is not None:
        print(f"주문 ID 1의 총액: {total}")
    else:
        print("주문 ID 1에 대한 주문을 찾을 수 없습니다.")