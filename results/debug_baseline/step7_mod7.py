from dataclasses import dataclass
from typing import List
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 재고 수량


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REFUNDED = "REFUNDED"  # 새로운 상태

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.created_at = datetime.datetime.now()  # 주문 생성 시각
        self.total = self.calculate_total()

    def calculate_total(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        return subtotal * (1 - self.discount_percent)

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Status: {self.status}, Created At: {self.created_at}"


@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # 환불 여부, 기본값 False


class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = Item(item_name, price, 0, stock)

    def get_stock(self, item_name):
        item = self.items.get(item_name)
        return item.stock if item else 0

    def reduce_stock(self, item_name, quantity):
        item = self.items.get(item_name)
        if not item:
            raise ValueError(f"재고에 {item_name}이(가) 없습니다.")
        if item.stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        item.stock -= quantity


class OrderManager:
    def __init__(self, inventory):
        self.orders = {}
        self.payments = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id, items, inventory):
        try:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)
        except ValueError as e:
            raise e  # Re-raise the stock-related ValueError

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            return  # Order not found, nothing to cancel

        if order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CONFIRMED
            order.total = order.calculate_total()

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_CONFIRMED:
            order.status = Order.STATUS_SHIPPED

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")

        if order.status != Order.STATUS_PENDING:
            raise ValueError("이미 결제된 주문입니다.")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = Order.STATUS_CONFIRMED
        order.total = order.calculate_total()
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None

    def refund_payment(self, order_id):
        payment = self.get_payment(order_id)
        if not payment:
            raise ValueError("결제를 찾을 수 없습니다.")

        if payment.refunded:
            raise ValueError("이미 환불된 결제입니다.")

        payment.refunded = True
        order = self.get_order(order_id)
        order.status = Order.STATUS_REFUNDED

    def get_refunded_orders(self):
        """
        refunded=True인 모든 주문을 반환합니다.
        """
        return [order for order in self.orders.values()
                if self.get_payment(order.order_id) and self.get_payment(order.order_id).refunded]

    def get_order_history(self):
        """
        모든 주문 이력을 반환합니다 (CANCELLED 주문 포함).
        주문 생성 시각(created_at) 기준으로 정렬합니다.
        """
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str):
        """
        지정된 상태의 주문만 반환합니다.
        """
        return [order for order in self.orders.values() if order.status == status]


# Example Usage (with new features)
if __name__ == '__main__':
    inventory = Inventory()
    inventory.add_item("Laptop", 1200, 5)
    inventory.add_item("Mouse", 25, 10)
    inventory.add_item("Keyboard", 75, 8)

    order_manager = OrderManager(inventory)

    try:
        # Create an order
        items = [
            Item("Laptop", 1200, 1, 0),
            Item("Mouse", 25, 2, 0),
            Item("Keyboard", 75, 1, 0)
        ]
        order_manager.add_order(1, items, inventory)

        # Create another order
        items2 = [
            Item("Laptop", 1200, 1, 0)
        ]
        order_manager.add_order(2, items2, inventory)

        # List orders
        print("\nOrders:")
        for order in order_manager.list_orders():
            print(order)

        # Apply discount
        order_manager.apply_discount(1, 0.1)

        # List orders after discount
        print("\nOrders after discount:")
        for order in order_manager.list_orders():
            print(order)

        # Get total
        total = order_manager.get_order_total(1)
        print(f"\nTotal for Order 1: {total:.2f}")

        # Confirm order
        order_manager.confirm_order(1)
        print("\nOrder 1 after confirmation:")
        print(order_manager.get_order(1))

        # Ship order
        order_manager.ship_order(1)
        print("\nOrder 1 after shipping:")
        print(order_manager.get_order(