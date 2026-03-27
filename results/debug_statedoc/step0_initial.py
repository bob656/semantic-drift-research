class Order:
    def __init__(self, order_id: int, items: list[str], total: float):
        """
        주문 정보를 나타내는 클래스.

        Args:
            order_id: 주문 ID (정수).
            items: 주문에 포함된 품목 목록 (문자열 리스트).
            total: 주문 총액 (실수).
        """
        self.order_id = order_id
        self.items = items
        self.total = total


class OrderManager:
    """
    주문 관리 기능을 제공하는 클래스.
    """

    def __init__(self):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders: dict[int, Order] = {}  # order_id를 키로 사용

    def add_order(self, order_id: int, items: list[str], total: float) -> None:
        """
        새로운 주문 정보를 시스템에 추가합니다.

        Args:
            order_id: 주문 ID.
            items: 주문에 포함된 품목 목록.
            total: 주문 총액.

        Raises:
            ValueError: order_id가 이미 존재하는 경우 또는 total이 음수인 경우.
        """
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        if total < 0:
            raise ValueError("Total must be non-negative")
        self.orders[order_id] = Order(order_id, items, total)

    def get_order(self, order_id: int) -> Order | None:
        """
        특정 주문 ID에 해당하는 주문 정보를 조회합니다.

        Args:
            order_id: 조회할 주문 ID.

        Returns:
            주문 정보 (Order 객체). 주문이 존재하지 않으면 None을 반환합니다.
        """
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """
        특정 주문 ID에 해당하는 주문 정보를 삭제합니다.

        Args:
            order_id: 삭제할 주문 ID.

        Raises:
            ValueError: order_id가 존재하지 않는 경우.
        """
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        del self.orders[order_id]

    def list_orders(self) -> list[Order]:
        """
        시스템에 저장된 모든 주문 정보를 목록으로 반환합니다.

        Returns:
            모든 주문 정보를 담은 리스트 (Order 객체 리스트).
        """
        return list(self.orders.values())


# 사용 예시
order_manager = OrderManager()

# 주문 추가
try:
    order_manager.add_order(1, ["item1", "item2"], 100.0)
    order_manager.add_order(2, ["item3"], 50.0)
except ValueError as e:
    print(f"Error: {e}")

# 주문 조회
order1 = order_manager.get_order(1)
if order1:
    print(f"Order 1: {order1.order_id}, Items: {order1.items}, Total: {order1.total}")

# 주문 목록 확인
all_orders = order_manager.list_orders()
print(f"All Orders: {all_orders}")

# 주문 취소
try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(f"Error: {e}")

# 주문 목록 확인 (취소 후)
all_orders = order_manager.list_orders()
print(f"All Orders after cancellation: {all_orders}")

# 예외 처리 예시
try:
    order_manager.add_order(2, ["item4"], -10.0)
except ValueError as e:
    print(f"Error: {e}")