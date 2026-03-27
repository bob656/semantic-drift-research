from dataclasses import dataclass
from typing import List

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

    def __init__(self, order_id, items, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.status = status
        self.discount_percent = 0.0
        self.total = self.calculate_total()

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}"

    def calculate_total(self):
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method


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
        return list(self.orders.values())

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문이 존재하지 않습니다.")

        if abs(amount - order.total) > 0.01:  # Allow for small floating-point differences
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total:.2f}, 결제 금액: {amount:.2f}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[self.next_payment_id] = payment
        self.next_payment_id += 1
        order.status = Order.STATUS_CONFIRMED
        order.total = order.calculate_total()  # Recalculate total in case of discount changes
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None


# Example Usage
inventory = Inventory()
inventory.add_item("Laptop", 1200, 5)
inventory.add_item("Mouse", 25, 10)
inventory.add_item("Keyboard", 75, 8)

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
print("\nOrders:")
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
print("\nOrders after cancellation:")
for order in order_manager.list_orders():
    print(order)

# Process payment for order 1
try:
    payment = order_manager.process_payment(1, order_manager.get_order(1).total, "Credit Card")
    print(f"\nPayment processed: {payment}")
    print(f"Order 1 status after payment: {order_manager.get_order(1).status}")
except ValueError as e:
    print(f"Payment Error: {e}")

# Get payment for order 1
payment = order_manager.get_payment(1)
if payment:
    print(f"\nPayment details for order 1: {payment}")
else:
    print("\nNo payment found for order 1.")

print("\nInventory after order:")
print(inventory.items)