class Order:
    """
    주문 정보를 나타내는 클래스입니다.
    """
    def __init__(self, order_id: int, items: list['Item']):
        """
        Order 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID
            items (list[Item]): 주문 항목 목록
        """
        self.order_id = order_id
        self.items = items
        self.discount_percent = 0.0
        self.total = self.calculate_total()
        self.status = "PENDING"  # 초기 상태를 PENDING으로 설정

    def calculate_total(self):
        """
        주문 항목의 총 가격을 계산합니다.
        """
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)


class Item:
    """
    주문 항목을 나타내는 클래스입니다.
    """
    def __init__(self, name: str, price: float, quantity: int):
        """
        Item 객체를 초기화합니다.

        Args:
            name (str): 항목 이름
            price (float): 항목 가격
            quantity (int): 항목 수량
        """
        self.name = name
        self.price = price
        self.quantity = quantity


class OrderManager:
    """
    주문 데이터 저장소를 관리하는 클래스입니다.
    """
    def __init__(self):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders = {}  # 주문 데이터를 저장할 딕셔너리 (order_id: Order)

    def add_order(self, order_id: int, items: list['Item']) -> None:
        """
        주문을 추가합니다.

        Args:
            order_id (int): 주문 ID
            items (list[Item]): 주문 항목 목록

        Raises:
            ValueError: order_id가 중복된 경우
            TypeError: items가 Item 객체 목록이 아닌 경우
        """
        if not isinstance(order_id, int):
            raise TypeError("order_id must be an integer")
        if not isinstance(items, list):
            raise TypeError("items must be a list")
        if not all(isinstance(item, Item) for item in items):
            raise TypeError("items must be a list of Item objects")

        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists")

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id: int) -> 'Order' | None:
        """
        주문 ID를 기반으로 주문을 조회합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            Order | None: 주문 객체. 주문이 없으면 None을 반환합니다.
        """
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        """
        주문 상태를 PENDING에서 CONFIRMED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"

    def ship_order(self, order_id: int) -> None:
        """
        주문 상태를 CONFIRMED에서 SHIPPED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"

    def cancel_order(self, order_id: int) -> None:
        """
        주문 상태를 CANCELLED로 변경합니다.
        """
        order = self.get_order(order_id)
        if not order:
            return

        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        order.status = "CANCELLED"

    def list_orders(self) -> list[tuple[int, 'Order']]:
        """
        모든 주문 목록을 반환합니다.
        """
        return [(order_id, order) for order_id, order in self.orders.items()]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """
        주문에 할인율을 적용합니다.

        Args:
            order_id (int): 주문 ID
            discount_percent (float): 할인율 (0.0 ~ 1.0)

        Raises:
            ValueError: order_id가 존재하지 않거나 discount_percent가 범위를 벗어난 경우
        """
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")

        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """
        주문의 총액을 반환합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            float: 주문의 총액
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0