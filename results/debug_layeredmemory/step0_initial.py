from typing import List, Optional

class Order:
    """주문을 나타내는 클래스."""

    def __init__(self, order_id: int, items: List[str], total: float):
        """
        Order 객체를 초기화합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
            total: 주문 총액.
        """
        self.order_id = order_id
        self.items = items
        self.total = total

    def __repr__(self):
        """Order 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total})"


class OrderManager:
    """주문 관리 기능을 제공하는 클래스."""

    def __init__(self):
        """OrderManager 객체를 초기화합니다."""
        self.orders: dict[int, Order] = {}  # 주문 ID를 키로 사용하여 주문을 저장합니다.

    def add_order(self, order_id: int, items: List[str], total: float) -> Order:
        """주문을 추가합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
            total: 주문 총액.

        Returns:
            추가된 Order 객체.
        """
        order = Order(order_id, items, total)
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


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    order1 = order_manager.add_order(1, ["Laptop", "Mouse"], 1200.00)
    order2 = order_manager.add_order(2, ["Keyboard", "Monitor"], 500.00)

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