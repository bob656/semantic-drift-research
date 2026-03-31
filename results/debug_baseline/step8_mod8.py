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
    STATUS_PAID = "PAID"
    STATUS_REFUNDED = "REFUNDED"

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING, customer_id=None):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()
        self.created_at = datetime.datetime.now()
        self.customer_id = customer_id

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}, Created At: {self.created_at}, Customer ID: {self.customer_id}"


class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.refunded = False  # Added refunded flag


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
        self.customers = {}
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
        if not self.get_customer(customer_id):
            raise ValueError(f"고객 ID {customer_id}가 등록되지 않았습니다.")

        order_id = self.next_order_id
        self.next_order_id += 1
        order = Order(order_id, items)

        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                # Rollback: 주문 생성 실패 시 재고 복구
                for ordered_item in items:
                    try:
                        inventory.add_item(ordered_item.name, ordered_item.price, ordered_item.quantity)
                    except:
                        pass
                raise e

        self.orders[order_id] = order
        order.customer_id = customer_id
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            order.status = "CANCELLED"

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            order.status = "CONFIRMED"

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            order.status = "SHIPPED"

    def process_payment(self, order_id, amount, method):
        """
        Processes a payment for the given order ID.
        Raises ValueError if the order has already been paid for.
        """
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")

        if order.status in (Order.STATUS_REFUNDED, Order.STATUS_CANCELLED):
            raise ValueError(f"Cannot process payment for a cancelled or refunded order.")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.next_payment_id += 1
        self.payments[payment.payment_id] = payment
        order.status = Order.STATUS_PAID
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None

    def refund_payment(self, order_id):
        payment = self.get_payment(order_id)
        if payment:
            payment.refunded = True
            order = self.get_order(order_id)
            order.status = Order.STATUS_REFUNDED

    def get_order_history(self):
        """
        Returns all orders, including cancelled orders, sorted by creation time.
        """
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str):
        """
        Returns orders with the specified status.
        """
        return [order for order in self.orders.values() if order.status == status]

    def get_refunded_orders(self):
        """
        Returns all orders that have been refunded.
        """
        return [order for order in self.orders.values() if order.status == Order.STATUS_REFUNDED]

    def get_orders_by_customer(self, customer_id):
        """
        Returns all orders for a specific customer.
        """
        return [order for order in self.orders.values() if order.customer_id == customer_id]


# Example Usage
inventory = Inventory()
inventory.add_item("Laptop", 1200, 5)
inventory.add_item("Mouse", 25, 10)
inventory.add_item("Keyboard", 75, 8)

order_manager = OrderManager(inventory)

# Add a customer
customer = order_manager.add_customer("John Doe", "john.doe@example.com")
print(f"Customer added: {customer}")

# Create an order for the customer
items = [
    Item("Laptop", 1200, 1, 0),
    Item("Mouse", 25, 2, 0),
    Item("Keyboard", 75, 1, 0)