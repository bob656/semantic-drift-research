from dataclasses import dataclass
from typing import List

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # Added stock attribute


class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}"

    def calculate_total(self):
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


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
    def __init__(self, inventory: Inventory):
        self.orders = {}
        self.payments = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id, items: List[Item], inventory: Inventory):
        try:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)
        except ValueError as e:
            raise e  # Re-raise the ValueError from Inventory

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            print(f"Order with ID {order_id} not found.")
            return

        if order.status == Order.STATUS_SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            print(f"Order with ID {order_id} is already cancelled.")

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
            else:
                print(f"Order with ID {order_id} not found.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_PENDING:
                order.status = Order.STATUS_CONFIRMED
            else:
                print(f"Order with ID {order_id} is not in PENDING status.")
        else:
            print(f"Order with ID {order_id} not found.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_CONFIRMED:
                order.status = Order.STATUS_SHIPPED
            else:
                print(f"Order with ID {order_id} is not in CONFIRMED status.")
        else:
            print(f"Order with ID {order_id} not found.")

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")

        if amount != order.total:
            raise ValueError(f"결제 금액이 일치하지 않습니다. 주문 금액: {order.total:.2f}, 결제 금액: {amount:.2f}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[self.next_payment_id] = payment
        self.next_payment_id += 1
        return payment

    def get_payment(self, payment_id):
        return self.payments.get(payment_id)


# Example Usage
inventory = Inventory()
inventory.add_item("Laptop", 1200.00, 10)
inventory.add_item("Mouse", 25.00, 50)
inventory.add_item("Keyboard", 75.00, 30)

order_manager = OrderManager(inventory)

# List all orders (initially empty)
print("All Orders:")
for order in order_manager.list_orders():
    print(order)

# Create an order
items = [
    Item("Laptop", 1200.00, 1, 1),
    Item("Mouse", 25.00, 1, 1),
    Item("Keyboard", 75.00, 1, 1)
]

try:
    order_manager.add_order(1, items, inventory)
except ValueError as e:
    print(f"\nError adding order: {e}")
    exit()

# List all orders
print("\nAll Orders:")
for order in order_manager.list_orders():
    print(order)

# Check stock levels
print("\nStock Levels:")
print(f"Laptop: {inventory.get_stock('Laptop')}")
print(f"Mouse: {inventory.get_stock('Mouse')}")
print(f"Keyboard: {inventory.get_stock('Keyboard')}")

# Apply discount
order_manager.apply_discount(1, 0.1)

# Get total
total = order_manager.get_order_total(1)
print(f"\nTotal for order 1: {total:.2f}")

# Confirm and ship order
order_manager.confirm_order(1)
order_manager.ship_order(1)

# Cancel order
try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(f"\nError: {e}")

# Process payment
try:
    payment = order_manager.process_payment(1, order_manager.get_order(1).total, "Credit Card")
    print(f"\nPayment processed: {payment}")
except ValueError as e:
    print(f"\nError: {e}")

# Get payment details
payment = order_manager.get_payment(1)
if payment:
    print(f"\nPayment details for order 1: {payment}")

# Try to process payment with incorrect amount
try:
    order_manager.process_payment(1, order_manager.get_order(1).total + 1, "Credit Card")
except ValueError as e:
    print(f"\nError: {e}")