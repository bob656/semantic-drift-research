from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Item:
    """
    상품 정보를 나타내는 클래스입니다.

    Attributes:
        name (str): 상품 이름.
        price (float): 상품 가격.
        quantity (int): 상품 수량.
    """
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0, status: str = "PENDING"):
        """
        주문 정보를 나타내는 클래스입니다.

        Args:
            order_id (int): 주문 ID.
            items (List[Item]): 주문에 포함된 상품 목록.
            discount_percent (float): 할인율 (0.0 ~ 1.0). 기본값은 0.0입니다.
            status (str): 주문 상태. 기본값은 "PENDING"입니다.
        """
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        """
        주문 총액을 계산합니다.

        Returns:
            float: 주문 총액.
        """
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


class OrderManager:
    """
    주문 관리 기능을 제공하는 클래스입니다.
    """
    def __init__(self):
        """
        주문 관리자를 초기화합니다.
        """
        self.orders: dict[int, Order] = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        """
        새로운 주문을 추가합니다.

        Args:
            order_id (int): 주문 ID.
            items (List[Item]): 주문에 포함된 상품 목록.

        Raises:
            ValueError: 중복된 주문 ID가 사용된 경우.
        """
        if order_id in self.orders:
            raise ValueError("Duplicate order ID.")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        """
        주문 ID를 기반으로 주문 정보를 조회합니다.

        Args:
            order_id (int): 조회할 주문 ID.

        Returns:
            Optional[Order]: 주문 정보. 주문이 없으면 None을 반환합니다.

        Raises:
            KeyError: 주문이 존재하지 않을 경우 발생하지 않음.  None 반환.
        """
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """
        주문 ID를 기반으로 주문을 취소합니다.

        Args:
            order_id (int): 취소할 주문 ID.

        Raises:
            KeyError: 주문이 존재하지 않을 경우.
            ValueError: 주문이 배송 중인 경우.
        """
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        order.status = "CANCELLED"

    def list_orders(self) -> list[Order]:
        """
        시스템에 저장된 모든 주문 목록을 조회합니다.

        Returns:
            list[Order]: 주문 목록.
        """
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """
        주문에 할인율을 적용합니다.

        Args:
            order_id (int): 할인율을 적용할 주문 ID.
            discount_percent (float): 할인율 (0.0 ~ 1.0).

        Raises:
            KeyError: 주문이 존재하지 않을 경우.
            ValueError: 할인율이 범위를 벗어난 경우.
        """
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0.")
        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """
        주문 ID를 기반으로 주문의 최종 총액을 조회합니다.

        Args:
            order_id (int): 조회할 주문 ID.

        Returns:
            float: 주문의 최종 총액.

        Raises:
            KeyError: 주문이 존재하지 않을 경우.
        """
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        return self.orders[order_id].total

    def confirm_order(self, order_id: int) -> None:
        """
        주문의 상태를 PENDING에서 CONFIRMED로 변경합니다.

        Args:
            order_id (int): 상태를 변경할 주문 ID.

        Raises:
            KeyError: 주문이 존재하지 않을 경우.
            ValueError: 주문 상태가 PENDING가 아닐 경우.
        """
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "PENDING":
            raise ValueError(f"주문 상태가 PENDING가 아닙니다. 현재 상태: {order.status}")
        order.status = "CONFIRMED"

    def ship_order(self, order_id: int) -> None:
        """
        주문의 상태를 CONFIRMED에서 SHIPPED로 변경합니다.

        Args:
            order_id (int): 상태를 변경할 주문 ID.

        Raises:
            KeyError: 주문이 존재하지 않을 경우.
            ValueError: 주문 상태가 CONFIRMED가 아닐 경우.
        """
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "CONFIRMED":
            raise ValueError(f"주문 상태가 CONFIRMED가 아닙니다. 현재 상태: {order.status}")
        order.status = "SHIPPED"


# 사용 예제
order_manager = OrderManager()

try:
    order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 20.0, 1)])
    order_manager.add_order(2, [Item("item3", 5.0, 3)])

    order = order_manager.get_order(1)
    print(f"Order 1: {order.items}, Total: {order.total}, Status: {order.status}")

    order_manager.confirm_order(1)
    print(f"Order 1 Status: {order.status}")

    order_manager.apply_discount(1, 0.1)
    print(f"Order 1 with discount: {order.discount_percent}, Total: {order.total}, Status: {order.status}")

    total = order_manager.get_order_total(1)
    print(f"Order 1 total: {total}")

    order_manager.ship_order(1)
    print(f"Order 1 Status: {order.status}")

    # order_manager.cancel_order(1)  # This will raise a ValueError because the order is shipped
    # order_manager.cancel_order(2)
    # order_manager.cancel_order(1)

    orders = order_manager.list_orders()
    print(f"Remaining orders: {[order.order_id for order in orders]}")

    # 예외 발생 테스트
    # order_manager.add_order(1, [Item("item4", 5.0, 1)]) # Duplicate order ID
    # order_manager.apply_discount(1, 1.2) # Invalid discount percent
except ValueError as e:
    print(f"Error: {e}")
except KeyError as e:
    print(f"Error: {e}")