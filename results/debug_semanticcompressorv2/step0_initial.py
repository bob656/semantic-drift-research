from typing import List, Optional

class Order:
    def __init__(self, order_id: int, items: List[str], total: float):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[str], total: float) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items, total)

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

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()

    # 주문 추가
    manager.add_order(1, ["item1", "item2"], 10.5)
    manager.add_order(2, ["item3"], 5.0)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    # 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후 주문 목록 확인
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")