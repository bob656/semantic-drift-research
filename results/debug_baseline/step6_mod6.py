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

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()
        self.created_at = datetime.datetime.now()

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}, Created At: {self.created_at}"


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
        self.next_order_id = 1
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, items, inventory: Inventory):
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
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            return

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
        return None

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError("주문이 존재하지 않습니다.")
        if abs(amount - order.total) > 0.01:  # 부동 소수점 비교를 위한 오차 허용
            raise ValueError("결제 금액이 주문 총액과 일치하지 않습니다.")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.next_payment_id += 1
        self.payments[payment.payment_id] = payment
        order.status = "PAID"  # Changed from "CONFIRMED" to "PAID"
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None

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


# Example Usage
inventory = Inventory()
inventory.add_item("Laptop", 1200, 5)
inventory.add_item("Mouse", 25, 10)
inventory.add_item("Keyboard", 75, 8)

order_manager = OrderManager(inventory)

# Create an order
items = [
    Item("Laptop", 1200, 1, 0),
    Item("Mouse", 25, 2, 0),
    Item("Keyboard", 75, 1, 0)
]

try:
    order = order_manager.add_order(items, inventory)
    print(f"Order created with ID: {order.order_id}")
except ValueError as e:
    print(f"Error creating order: {e}")

# Get current stock of Laptop
laptop_stock = inventory.get_stock("Laptop")
print(f"Current stock of Laptop: {laptop_stock}")

# Confirm the order
order_manager.confirm_order(order.order_id)
print(f"Order {order.order_id} confirmed.")

# Ship the order
order_manager.ship_order(order.order_id)
print(f"Order {order.order_id} shipped.")

# Process payment for the order
try:
    payment = order_manager.process_payment(order.order_id, order.total, "Credit Card")
    print(f"Payment processed for order {order.order_id}: {payment}")
except ValueError as e:
    print(f"Payment error: {e}")

# Get the payment information
payment = order_manager.get_payment(order.order_id)
if payment:
    print(f"Payment information for order {order.order_id}: {payment}")
else:
    print(f"No payment found for order {order.order_id}")

# List all orders
print("\nAll orders:")
for order in order_manager.list_orders():
    print(order)

# Get order history
print("\nOrder History:")
for order in order_manager.get_order_history():
    print(order)

# Get orders by status
print("\nPending Orders:")
for order in order_manager.get_orders_by_status("PENDING"):
    print(order)

print("\nCancelled Orders:")
for order in order_manager.