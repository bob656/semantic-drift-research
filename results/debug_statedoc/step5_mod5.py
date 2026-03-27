from dataclasses import dataclass
from typing import Optional

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str


class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity


class Order:
    def __init__(self, order_id: int, items: list[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = self.calculate_total()
        self.status = "PENDING"  # Initial status

    def calculate_total(self) -> float:
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


class Inventory:
    def __init__(self):
        self.items: dict[str, (float, int)] = {}  # {item_name: (price, stock)}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        self.items[item_name] = (price, stock)

    def get_stock(self, item_name: str) -> int:
        if item_name not in self.items:
            return 0  # Or raise an exception if the item should exist
        return self.items[item_name][1]

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} not found in inventory.")
        price, stock = self.items[item_name]
        if stock < quantity:
            raise ValueError(f"Not enough stock for {item_name}. Available: {stock}, Requested: {quantity}")
        self.items[item_name] = (price, stock - quantity)


class OrderManager:
    def __init__(self, inventory: Inventory):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id: int, items: list[Item]) -> None:
        if order_id in self.orders:
            raise ValueError("Duplicate order ID.")

        for item in items:
            self.inventory.reduce_stock(item.name, item.quantity)

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        order.status = "CANCELLED"

        # Restore stock
        for item in order.items:
            self.inventory.add_item(item.name, item.price, item.quantity)

    def list_orders(self) -> list[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0.")
        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        return self.orders[order_id].total

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "PENDING":
            raise ValueError(f"주문 상태가 PENDING가 아닙니다. 현재 상태: {order.status}")
        order.status = "CONFIRMED"

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "CONFIRMED":
            raise ValueError(f"주문 상태가 CONFIRMED가 아닙니다. 현재 상태: {order.status}")
        order.status = "SHIPPED"

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]

        if abs(amount - order.total) > 0.01:  # Allow for slight floating-point inaccuracies
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = "CONFIRMED"  # Update order status after successful payment
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None


# 사용 예제
inventory = Inventory()
inventory.add_item("item1", 10.0, 10)
inventory.add_item("item2", 20.0, 5)
inventory.add_item("item3", 5.0, 10)

order_manager = OrderManager(inventory)

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

    payment = order_manager.process_payment(1, order.total, "credit_card")
    print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    print(f"Order 1 Status after payment: {order.status}")

    retrieved_payment = order_manager.get_payment(1)
    if retrieved_payment:
        print(f"Retrieved Payment: {retrieved_payment}")

    order_manager.ship_order(1)
    print(f"Order 1 Status: {order.status}")

    # order_manager.cancel_order(1)  # This will raise a ValueError because the order is shipped
    # order_manager.cancel_order(2)
    # order_manager.cancel_order(1)

    orders = order_manager.list_orders()
    print(f"Remaining orders: {[order.order_id for order in orders]}")

    # 예외 발생 테스트
    # order_manager.add_order(1