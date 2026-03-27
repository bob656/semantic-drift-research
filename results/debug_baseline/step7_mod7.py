from dataclasses import dataclass
from typing import List
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # Added stock attribute


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_PAID = "PAID"
    STATUS_REFUNDED = "REFUNDED"  # Added REFUNDED status

    def __init__(self, order_id, items, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.status = status
        self.discount_percent = 0.0
        self.total = self.calculate_total()
        self.created_at = datetime.datetime.now()  # Added created_at

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}, Created At: {self.created_at}"

    def calculate_total(self):
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # Added refunded attribute


class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = {"price": price, "stock": stock}

    def get_stock(self, item_name):
        return self.items.get(item_name, {}).get("stock", 0)

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items or self.items[item_name]["stock"] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name]["stock"] -= quantity


class OrderManager:
    def __init__(self, inventory):
        self.orders = {}
        self.payments = {}
        self.next_order_id = 1
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id, items):
        for item in items:
            self.inventory.reduce_stock(item.name, item.quantity)
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
        return None

    def list_orders(self):
        # Return only active orders (PENDING, CONFIRMED, SHIPPED)
        return [order for order in self.orders.values() if order.status not in (Order.STATUS_CANCELLED)]

    def get_order_history(self):
        # Return all orders, sorted by creation time
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status):
        return [order for order in self.orders.values() if order.status == status]

    def refund_payment(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order not found")

        payment = self.get_payment(order_id)
        if not payment:
            raise ValueError("Payment not found for this order")

        if payment.refunded:
            raise ValueError("Payment already refunded")

        payment.refunded = True
        order.status = Order.STATUS_REFUNDED

    def get_refunded_orders(self):
        refunded_orders = []
        for order in self.orders.values():
            payment = self.get_payment(order.order_id)
            if payment and payment.refunded:
                refunded_orders.append(order)
        return refunded_orders

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status == Order.STATUS_PAID:
            raise ValueError("Payment already processed for this order")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[self.next_payment_id] = payment
        self.next_payment_id += 1
        order.status = Order.STATUS_PAID
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None


# Example Usage (same as before, with added functionality)
inventory = Inventory()
order_manager = OrderManager(inventory)

# Create an order
items = [
    Item("Laptop", 1200, 1, 1),
    Item("Mouse", 25, 1, 1),
    Item("Keyboard", 75, 1, 1)
]

# Add the order
order_manager.add_order(1, items)

# List orders
print("\nActive Orders:")
for order in order_manager.list_orders():
    print(order)

# Get total for order 2
total = order_manager.get_order_total(1)
if total:
    print(f"\nTotal for Order 1: {total:.2f}")
else:
    print("Order not found")

# Confirm order 2
order_manager.confirm_order(1)
print("\nOrder 1 after confirmation:")
print(order_manager.get_order(1))

# Ship order 2
order_manager.ship_order(1)
print("\nOrder 1 after shipping:")
print(order_manager.get_order(1))

# Cancel order 1
try:
    order_manager.cancel_order(1)
    print("\nOrder 1 cancelled successfully:")
    print(order_manager.get_order(1))
except ValueError as e:
    print(f"Error cancelling order: {e}")

# Attempt to cancel a shipped order (should raise ValueError)
try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(f"\nExpected Error: {e}")

# List orders after cancellation
print("\nActive Orders after cancellation:")
for order in order_manager.list_orders():
    print(order)

# Get order history
print("\nOrder History:")
for order in order_manager.get_order_history():
    print(order)

# Get orders by status
print("\nPending Orders:")
for order in order_manager.get_orders_by_status(Order.STATUS_PENDING):
    print(order)

# Process payment for order