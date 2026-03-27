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
    STATUS_REFUNDED = "REFUNDED"  # 새 상태 추가

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING, customer_id=None):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.created_at = datetime.datetime.now()  # 주문 생성 시각
        self.customer_id = customer_id
        self.total = self.calculate_total()

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
        if item:
            return item.stock
        else:
            return 0

    def reduce_stock(self, item_name, quantity):
        item = self.items.get(item_name)
        if not item:
            raise ValueError(f"Item {item_name} not found in inventory.")
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
        self.customers = {}  # 고객 정보 저장
        self.next_order_id = 1
        self.next_payment_id = 1
        self.next_customer_id = 1
        self.inventory = inventory

    def add_customer(self, name, email):
        customer_id = self.next_customer_id
        self.next_customer_id += 1
        customer = Customer(customer_id, name, email)
        self.customers[customer_id] = customer
        return customer

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def add_order(self, items, inventory: Inventory, customer_id):
        if customer_id not in self.customers:
            raise ValueError(f"고객 ID {customer_id}를 찾을 수 없습니다.")

        order_id = self.next_order_id
        self.next_order_id += 1
        order = Order(order_id, items, status=Order.STATUS_PENDING, customer_id=customer_id)

        # 재고 차감
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)

        self.orders[order_id] = order
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_CANCELLED  # CANCELLED 상태 유지

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        return order.total

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_CONFIRMED

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_SHIPPED

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        if order.total != amount:
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다.")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.next_payment_id += 1
        self.payments[payment.payment_id] = payment
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None

    def refund_payment(self, order_id):
        payment = self.get_payment(order_id)
        if not payment:
            raise ValueError(f"결제를 찾을 수 없습니다.")
        if payment.refunded:
            raise ValueError(f"이미 환불된 결제입니다.")

        payment.refunded = True
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다.")
        order.status = Order.STATUS_REFUNDED

    def get_order_history(self):
        return list(self.orders.values())

    def get_orders_by_customer(self, customer_id):
        customer_orders = []
        for order_id, order in self.orders.items():
            if order.customer_id == customer_id:
                customer_orders.append(order)
        return customer_orders

    def get_orders_by_status(self, status):
        orders_by_status = []
        for order_id, order in self.orders.items():
            if order.status == status:
                orders_by_status.append(order)
        return orders_by_status


# Example Usage
inventory = Inventory()
inventory.add_item("Webcam", 50.00, 10)
inventory.add_item("Microphone", 100.00, 5)
inventory.add_item("Keyboard", 75.00, 8)
inventory.add_item("Mouse", 25.00, 12)

order_manager = OrderManager(inventory)

# Add a customer
customer1 = order_manager.add_customer("Alice Smith", "alice.smith@example.com")
customer2 = order_manager.add_customer("Bob Johnson", "bob.johnson@example.com")

# Create an order for customer1
items = [
    Item("Webcam", 50.00, 1, 0),
    Item("Microphone", 100.00, 1, 0),
]
order1 = order_manager.add_order(items,