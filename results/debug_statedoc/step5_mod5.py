from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Item:
    name: str
    price: float
    quantity: int


@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str


class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = self._calculate_total()
        self.status = "PENDING"
        self.discount_percent = 0.0
        self.payment: Optional[Payment] = None

    def _calculate_total(self) -> float:
        total = sum(item.price * item.quantity for item in self.items)
        return total * (1 - self.discount_percent)


class Inventory:
    def __init__(self):
        self.items: dict[str, int] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        self.items[item_name] = stock

    def get_stock(self, item_name: str) -> int:
        return self.items.get(item_name, 0)

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if self.get_stock(item_name) < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name] -= quantity


class OrderManager:
    def __init__(self, inventory: Inventory):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")

        for item in items:
            if self.inventory.get_stock(item.name) < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")

        order = Order(order_id, items)
        self.orders[order_id] = order

        for item in items:
            self.inventory.reduce_stock(item.name, item.quantity)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        order.status = "CANCELLED"

        for item in order.items:
            self.inventory.add_item(item.name, item.price, item.quantity)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "PENDING":
            raise ValueError("주문 상태가 PENDING가 아니면 확인할 수 없습니다.")
        order.status = "CONFIRMED"
        order.total = order._calculate_total()

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "CONFIRMED":
            raise ValueError("주문 상태가 CONFIRMED가 아니면 배송할 수 없습니다.")
        order.status = "SHIPPED"

    def list_orders(self) -> list[tuple[int, str, float]]:
        return [(order.order_id, order.status, order.total) for order in self.orders.values()]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = self.orders[order_id]._calculate_total()

    def get_order_total(self, order_id: int) -> float:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if not order:
            raise KeyError(f"Order ID {order_id} not found.")

        if abs(amount - order.total) > 0.001:  # Allow for small floating-point differences
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[self.next_payment_id] = payment
        self.next_payment_id += 1
        order.payment = payment
        order.status = "CONFIRMED"
        order.total = order._calculate_total()
        return payment

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)


# 사용 예제
inventory = Inventory()
inventory.add_item("item1", 10.0, 5)
inventory.add_item("item2", 5.0, 3)
inventory.add_item("item3", 20.0, 2)

order_manager = OrderManager(inventory)

try:
    order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 5.0, 3)])
    order_manager.add_order(2, [Item("item3", 20.0, 1)])

    order1 = order_manager.get_order(1)
    print(f"Order 1: {order1.order_id}, Items: {[item.name for item in order1.items]}, Total: {order1.total}, Status: {order1.status}")

    order_manager.apply_discount(1, 0.1)
    print(f"Order 1 discounted: {order1.total}")

    print(f"Order 1 total: {order_manager.get_order_total(1)}")

    payment1 = order_manager.process_payment(1, order1.total, "credit card")
    print(f"Payment for Order 1: {payment1.payment_id}, Amount: {payment1.amount}, Method: {payment1.method}")
    print(f"Order 1 status after payment: {order1.status}")

    order_manager.confirm_order(1)
    print(f"Order 1 confirmed: {order1.status}")

    order_manager.ship_order(1)
    print(f"Order 1 shipped: {order1.status}")

    order_manager.cancel_order(2)
    print(f"Order 2 cancelled: {order_manager.get_order(2).status}")

    orders = order_manager.list_orders()
    print(f"Remaining Orders: {orders}")

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

    try:
        order_manager.ship