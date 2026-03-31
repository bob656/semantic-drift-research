class Order:
    def __init__(self, order_id: int, items: list[str], total: float):
        self.order_id = order_id
        self.items = items
        self.total = total

    def __repr__(self):
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total})"


class OrderManager:
    def __init__(self):
        self.orders = {}  # order_id를 키로 사용

    def add_order(self, order_id: int, items: list[str], total: float) -> None:
        """주문 추가. order_id 중복 검사 수행."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items, total)

    def get_order(self, order_id: int) -> Order | None:
        """주문 ID에 해당하는 주문 조회. 주문이 없으면 None 반환."""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """주문 ID에 해당하는 주문 취소 (삭제). 주문이 없으면 아무런 동작을 하지 않음."""
        if order_id in self.orders:
            del self.orders[order_id]

    def list_orders(self) -> list[Order]:
        """모든 주문 목록 반환."""
        return list(self.orders.values())


# 사용 예제
if __name__ == "__main__":
    # OrderManager 인스턴스 생성
    order_manager = OrderManager()

    # 주문 추가
    try:
        order_manager.add_order(1, ["item1", "item2"], 100.0)
        order_manager.add_order(2, ["item3"], 50.0)
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
        print(f"Order ID: {order.order_id}")

    # 주문 취소
    order_manager.cancel_order(1)

    # 취소된 주문 조회 (None 반환)
    order = order_manager.get_order(1)
    print(f"Order ID 1 exists: {order is None}")