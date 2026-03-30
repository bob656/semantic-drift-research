class Order:
    def __init__(self, order_id: int, items: list[str], total: float):
        """
        주문 정보를 나타내는 클래스입니다.

        Args:
            order_id (int): 주문 ID (고유 식별자)
            items (list[str]): 주문 상품 목록 (각 상품은 문자열로 표현)
            total (float): 주문 총액
        """
        self.order_id = order_id
        self.items = items
        self.total = total


class OrderManager:
    """
    주문 정보를 저장하고 관리하는 클래스입니다.
    """

    def __init__(self):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders: dict[int, Order] = {}

    def add_order(self, order_id: int, items: list[str], total: float) -> None:
        """
        새로운 주문 정보를 시스템에 추가합니다.

        Args:
            order_id (int): 주문 ID
            items (list[str]): 주문 상품 목록
            total (float): 주문 총액

        Raises:
            ValueError: order_id가 이미 존재하거나 total이 음수인 경우
        """
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        if total < 0:
            raise ValueError("Total cannot be negative.")
        self.orders[order_id] = Order(order_id, items, total)

    def get_order(self, order_id: int) -> Order | None:
        """
        특정 주문 ID를 기반으로 주문 정보를 조회합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            Order: 주문이 존재하는 경우 해당 Order 객체, 주문이 존재하지 않는 경우 None
        """
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """
        특정 주문 ID를 기반으로 주문을 시스템에서 삭제합니다.

        Args:
            order_id (int): 주문 ID

        Raises:
            KeyError: 주문이 존재하지 않는 경우
        """
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        del self.orders[order_id]

    def list_orders(self) -> list[Order]:
        """
        시스템에 저장된 모든 주문 정보를 목록 형태로 조회합니다.

        Returns:
            list[Order]: 모든 주문 목록
        """
        return list(self.orders.values())


# 사용 예제
order_manager = OrderManager()

try:
    order_manager.add_order(1, ["item1", "item2"], 100.0)
    order_manager.add_order(2, ["item3"], 50.0)

    order1 = order_manager.get_order(1)
    print(f"Order 1: {order1.order_id}, Items: {order1.items}, Total: {order1.total}")

    order_manager.cancel_order(1)

    orders = order_manager.list_orders()
    print(f"Remaining Orders: {[order.order_id for order in orders]}")

    # 예외 처리 테스트
    try:
        order_manager.add_order(1, ["item4"], 75.0)  # 중복 ID
    except ValueError as e:
        print(f"Error: {e}")

    try:
        order_manager.cancel_order(3)  # 존재하지 않는 ID
    except KeyError as e:
        print(f"Error: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")