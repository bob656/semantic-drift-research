class Item:
    """
    주문 상품 정보를 나타내는 클래스입니다.

    Args:
        name (str): 상품 이름
        price (float): 상품 가격
        quantity (int): 상품 수량
    """
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity


class Order:
    def __init__(self, order_id: int, items: list[Item]):
        """
        주문 정보를 나타내는 클래스입니다.

        Args:
            order_id (int): 주문 ID (고유 식별자)
            items (list[Item]): 주문 상품 목록
        """
        self.order_id = order_id
        self.items = items
        self.discount_percent = 0.0
        self.total = self._calculate_total()

    def _calculate_total(self) -> float:
        """
        주문 총액을 계산합니다.

        Returns:
            float: 주문 총액
        """
        total = sum(item.price * item.quantity for item in self.items)
        return total * (1 - self.discount_percent)


class OrderManager:
    """
    주문 정보를 저장하고 관리하는 클래스입니다.
    """

    def __init__(self):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders: dict[int, Order] = {}

    def add_order(self, order_id: int, items: list[Item]) -> None:
        """
        새로운 주문 정보를 시스템에 추가합니다.

        Args:
            order_id (int): 주문 ID
            items (list[Item]): 주문 상품 목록

        Raises:
            ValueError: order_id가 이미 존재하면
        """
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items)

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

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """
        주문에 할인을 적용합니다.

        Args:
            order_id (int): 주문 ID
            discount_percent (float): 할인 비율 (0.0 ~ 1.0)

        Raises:
            KeyError: 주문이 존재하지 않는 경우
            ValueError: discount_percent가 범위를 벗어난 경우
        """
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = self.orders[order_id]._calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """
        특정 주문 ID의 최종 총액을 반환합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            float: 주문의 최종 총액
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0


# 사용 예제
order_manager = OrderManager()

try:
    order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 5.0, 3)])
    order_manager.add_order(2, [Item("item3", 20.0, 1)])

    order1 = order_manager.get_order(1)
    print(f"Order 1: {order1.order_id}, Items: {[item.name for item in order1.items]}, Total: {order1.total}")

    order_manager.apply_discount(1, 0.1)
    print(f"Order 1 discounted: {order1.total}")

    print(f"Order 1 total: {order_manager.get_order_total(1)}")

    order_manager.cancel_order(1)

    orders = order_manager.list_orders()
    print(f"Remaining Orders: {[order.order_id for order in orders]}")

    # 예외 처리 테스트
    try:
        order_manager.add_order(1, [Item("item4", 10.0, 1)])  # 중복 ID
    except ValueError as e:
        print(f"Error: {e}")

    try:
        order_manager.cancel_order(3)  # 존재하지 않는 ID
    except KeyError as e:
        print(f"Error: {e}")

    try:
        order_manager.apply_discount(1, 1.2)
    except ValueError as e:
        print(f"Error: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")