from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

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
        self.refunded = False  # 환불 여부 필드 추가


class Order:
    """주문을 나타내는 클래스."""

    def __init__(self, order_id: int, items: List[Item], customer_id: int):
        """
        Order 객체를 초기화합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
            customer_id: 고객 ID.
        """
        self.order_id = order_id
        self.items = items
        self.customer_id = customer_id
        self.discount_percent = 0.0  # 할인율을 추가합니다.
        self.total = self.calculate_total()
        self.status: str = "PENDING"  # 주문 상태를 추가합니다.
        self.created_at: datetime = datetime.now()  # 주문 생성 시각을 추가합니다.

    def calculate_total(self) -> float:
        """주문 총액을 계산합니다."""
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)

    def __repr__(self):
        """Order 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, discount_percent={self.discount_percent}, total={self.total}, status={self.status}, created_at={self.created_at}, customer_id={self.customer_id})"


class Customer:
    """고객 정보를 나타내는 클래스."""
    def __init__(self, customer_id: int, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email


class OrderManager:
    """주문 관리 기능을 제공하는 클래스."""

    def __init__(self):
        """OrderManager 객체를 초기화합니다."""
        self.orders: dict[int, Order] = {}  # 주문 ID를 키로 사용하여 주문을 저장합니다.
        self.customers: dict[int, Customer] = {} # 고객 ID를 키로 사용하여 고객 정보를 저장합니다.
        self.payments: dict[int, Payment] = {} # 결제 ID를 키로 사용하여 결제 정보를 저장합니다.

    def add_customer(self, customer_id: int, name: str, email: str) -> Customer:
        """고객을 추가합니다.

        Args:
            customer_id: 고객 ID.
            name: 고객 이름.
            email: 고객 이메일.

        Returns:
            추가된 Customer 객체.
        """
        customer = Customer(customer_id, name, email)
        self.customers[customer_id] = customer
        return customer

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """고객 ID로 고객 정보를 조회합니다.

        Args:
            customer_id: 조회할 고객 ID.

        Returns:
            고객이 있으면 Customer 객체를 반환하고, 없으면 None을 반환합니다.
        """
        return self.customers.get(customer_id)

    def add_order(self, order_id: int, items: List[Item], inventory: 'Inventory', customer_id: int) -> Order:
        """주문을 추가합니다.

        Args:
            order_id: 주문 ID.
            items: 주문 품목 목록.
            inventory: 재고 관리 객체.
            customer_id: 고객 ID.

        Returns:
            추가된 Order 객체.
        """
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"등록되지 않은 고객 ID: {customer_id}")

        for item in items:
            if inventory.get_stock(item.name) < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)

        order = Order(order_id, items, customer_id)
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

    def cancel_order(self, order_id: int):
        """주문을 취소합니다.

        Args:
            order_id: 취소할 주문 ID.
        """
        order = self.get_order(order_id)
        if order:
            order.status = "CANCELLED"

    def apply_discount(self, order_id: int, discount_percent: float):
        """주문에 할인을 적용합니다.

        Args:
            order_id: 할인 적용할 주문 ID.
            discount_percent: 할인율.
        """
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """주문 총액을 반환합니다.

        Args:
            order_id: 주문 ID.

        Returns:
            주문 총액.
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def confirm_order(self, order_id: int):
        """주문을 확정합니다.

        Args:
            order_id: 확정할 주문 ID.
        """
        order = self.get_order(order_id)
        if order:
            order.status = "CONFIRMED"

    def ship_order(self, order_id: int):
        """주문을 배송합니다.

        Args:
            order_id: 배송할 주문 ID.
        """
        order = self.get_order(order_id)
        if order:
            order.status = "SHIPPED"

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        """결제를 처리합니다."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문 ID {order_id}를 찾을 수 없습니다.")

        if order.status != "PENDING":
            raise ValueError(f"주문 ID {order_id}는 이미 처리된 상태입니다.")

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

    def refund_payment(self, order_id: int):
        """결제를 환불합니다.

        Args:
            order_id: 환불할 주문 ID.
        """
        order = self.get_order(order_id)
        if order:
            payment = self.get_payment(order_id)
            if payment:
                payment.refunded = True
                order.status = "REFUNDED"
                order.total = order.calculate_total()

    def get_order_history(self, customer_id: int) -> List[Order]:
        """특정 고객의 주문 내역을 반환합니다.

        Args:
            customer_id: 고객 ID.