from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Item:
    """
    품목 정보를 나타내는 클래스입니다.

    Args:
        name (str): 품목 이름
        price (float): 품목 가격
        quantity (int): 품목 수량
    """
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id: int, items: List[Item]):
        """
        주문 정보를 나타내는 클래스입니다.

        Args:
            order_id (int): 주문 ID
            items (List[Item]): 주문 품목 목록
        """
        self.order_id = order_id
        self.items = items
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        """
        주문 총액을 계산합니다.

        Returns:
            float: 주문 총액
        """
        return sum(item.price * item.quantity for item in self.items)


class OrderManager:
    """
    주문 목록을 관리하는 클래스입니다.
    """

    def __init__(self):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders: dict[int, Order] = {}  # order_id를 키로 사용하는 dictionary

    def add_order(self, order_id: int, items: List[Item]) -> None:
        """
        새로운 주문을 추가합니다.

        Args:
            order_id (int): 주문 ID
            items (List[Item]): 주문 품목 목록

        Raises:
            ValueError: order_id가 이미 존재하는 경우
        """
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        """
        주문 ID에 해당하는 주문 정보를 조회합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            Optional[Order]: 주문 정보. 주문이 존재하지 않으면 None을 반환합니다.
        """
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """
        주문 ID에 해당하는 주문을 취소합니다.

        Args:
            order_id (int): 주문 ID
        """
        if order_id not in self.orders:
            print(f"Error: Order ID {order_id} not found.")
            return
        del self.orders[order_id]

    def list_orders(self) -> list[Order]:
        """
        시스템에 저장된 모든 주문 정보를 목록으로 반환합니다.

        Returns:
            list[Order]: 주문 목록
        """
        return list(self.orders.values())


# 사용 예시
order_manager = OrderManager()

# 주문 추가
try:
    order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 20.0, 1)])
    order_manager.add_order(2, [Item("item3", 5.0, 3)])
except ValueError as e:
    print(e)

# 주문 조회
order = order_manager.get_order(1)
if order:
    print(f"Order 1: {order.order_id}, Items: {order.items}, Total: {order.total}")
else:
    print("Order not found.")

# 주문 목록 확인
orders = order_manager.list_orders()
print("All Orders:", [order.order_id for order in orders])

# 주문 취소
order_manager.cancel_order(1)

# 주문 목록 확인 (취소 후)
orders = order_manager.list_orders()
print("All Orders after cancellation:", [order.order_id for order in orders])