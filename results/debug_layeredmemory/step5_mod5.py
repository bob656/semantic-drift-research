from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    """주문 품목을 나타내는 클래스."""
    name: str
    price: float
    quantity: int
    stock: int  # 재고 수량


class Payment:
    """결제를 나타내는 클래스."""
    def __init__(self, payment_id: int, order_id: int, amount: float, method: str):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method


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
        self.status: str = "PENDING"  # 주문 상태를 추가합니다.

    def calculate_total(self) -> float:
        """주문 총액을 계산합니다."""
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)

    def __repr__(self):
        """Order 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, discount_percent={self.discount_percent}, total={self.total}, status={self.status})"


class OrderManager:
    """주문 관리 기능을 제공하는 클래스."""

    def __init__(self):
        """OrderManager 객체를 초기화합니다."""
        self.orders: dict[int, Order] = {}  # 주문 ID를 키로 사용하여 주문을 저장합니다.
        self.payments: dict[int, Payment] = {} # 결제 ID를 키로 사용하여 결제 정보를 저장합니다.

    def add_order(self, order_id: int, items: List[Item], inventory: 'Inventory') -> Order:
        """주문을 추가합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
            inventory: 재고 관리 객체.

        Returns:
            추가된 Order 객체.
        """
        for item in items:
            if inventory.get_stock(item.name) < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)

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

    def cancel_order(self, order_id: int) -> None:
        """주문을 취소합니다.

        Args:
            order_id: 취소할 주문 ID.

        Raises:
            ValueError: 주문이 배송 중인 경우.
        """
        order = self.get_order(order_id)
        if not order:
            return  # 주문이 없으면 아무것도 하지 않습니다.

        if order.status in ("SHIPPED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        if order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"
            order.total = order.calculate_total() # 할인 적용 후 총액 재계산

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

    def confirm_order(self, order_id: int) -> None:
        """주문 상태를 PENDING에서 CONFIRMED로 변경합니다."""
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            order.total = order.calculate_total()

    def ship_order(self, order_id: int) -> None:
        """주문 상태를 CONFIRMED에서 SHIPPED로 변경합니다."""
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        """결제를 처리합니다.

        Args:
            order_id: 결제할 주문 ID.
            amount: 결제 금액.
            method: 결제 방법.

        Returns:
            결제 객체.

        Raises:
            ValueError: 결제 금액이 주문 총액과 일치하지 않는 경우.
        """
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문이 존재하지 않습니다.")

        if order.total != amount:
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment = Payment(len(self.payments) + 1, order_id, amount, method)
        self.payments[len(self.payments)] = payment
        order.status = "PAID"
        order.total = order.calculate_total()
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        """주문 ID로 결제 정보를 조회합니다.

        Args:
            order_id: 조회할 주문 ID.

        Returns:
            결제가 있으면 Payment 객체를 반환하고, 없으면 None을 반환합니다.
        """
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None


class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = {'price': price, 'stock': stock}

    def get_stock(self, item_name):
        if item_name in self.items:
            return self.items[item_name]['stock']
        else:
            return 0

    def reduce_stock(self, item_name, quantity):
        if item_name in self.items:
            if self.items[item_name]['stock'] < quantity:
                raise ValueError(f"재고 부족: {item_name}")
            self.items[item_name]['stock'] -= quantity
        else:
            raise ValueError(f"재고에 없는 상품: {item_name}")


# 사용 예제
if __name__ == '__main__':
    inventory = Inventory()
    inventory.add_item("Product A", 10.0, 5)

    order_manager = OrderManager()
    order = order_manager.add_order(1, [Item("Product A", 10.0, 1, 5)], inventory)

    try:
        payment = order_manager.process_payment(1, 10.0, "Credit Card")
        print(f"결제 성공: {payment}")
    except ValueError as e:
        print(f"결제 실패: {e}")