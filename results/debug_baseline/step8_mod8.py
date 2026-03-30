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

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING, customer_id=None):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.created_at = datetime.datetime.now()  # 주문 생성 시각
        self.total = self.calculate_total()
        self.customer_id = customer_id

    def calculate_total(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        return subtotal * (1 - self.discount_percent)

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Status: {self.status}, Created At: {self.created_at}, Customer ID: {self.customer_id}"


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


class Customer:
    def __init__(self, customer_id, name, email):
        self.customer_id = customer_id
        self.name = name
        self.email = email

    def __str__(self):
        return f"Customer ID: {self.customer_id}, Name: {self.name}, Email: {self.email}"


class OrderManager:
    def __init__(self, inventory):
        self.orders = {}
        self.payments = {}
        self.next_payment_id = 1
        self.inventory = inventory
        self.customers = {}  # 고객 정보 저장

    def add_customer(self, customer_id, name, email):
        self.customers[customer_id] = Customer(customer_id, name, email)

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def add_order(self, order_id, items, inventory, customer_id):
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"고객 {customer_id}를 찾을 수 없습니다.")

        try:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)
        except ValueError as e:
            raise e  # Re-raise the stock-related ValueError

        order = Order(order_id, items, status=Order.STATUS_PENDING, customer_id=customer_id)
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
            raise ValueError("주문 상태가 취소될 수 없습니다.")

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")
        return order.total

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_CONFIRMED

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_SHIPPED

    def process_payment(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문을 찾을 수 없습니다.")
        # Payment processing logic here
        payment_id = self.next_payment_id
        self.next_payment_id += 1
        payment = Payment(payment_id, order.order_id, order.total, "Credit Card")
        self.payments[payment_id] = payment
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

    def get_orders_by_customer(self, customer_id):
        """
        특정 고객의 모든 주문을 반환합니다.
        """
        return [order for order in self.orders.values() if order.customer_id == customer_id]


# Example Usage (with new features)
if __name__ == '__main__':
    inventory = Inventory()
    inventory.add_item("Laptop", 1200, 5)
    inventory.add_item("Mouse", 25, 10)
    inventory.add_item("Keyboard", 75, 8)

    order_manager = OrderManager(inventory)

    # Add a customer
    order_manager.add_customer(1, "John Doe", "john.doe@example.com")
    order_manager.add_customer(2, "Jane Smith", "jane.smith@example.com")

    try:
        # Create an order for customer 1
        items = [
            Item("Laptop", 1200, 1, 0),
            Item("Mouse", 25, 2, 0),
            Item("Keyboard", 75, 1, 0)
        ]
        order_manager.add_order(1, items, inventory, 1)

        # Create another order for customer 2
        items2 = [
            Item("Laptop", 1200, 1,