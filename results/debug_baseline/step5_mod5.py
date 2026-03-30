from dataclasses import dataclass
from typing import List

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

    def calculate_total(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        return subtotal * (1 - self.discount_percent)

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Status: {self.status}"


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
            raise ValueError("주문이 존재하지 않습니다.")

        if abs(amount - order.total) > 0.01:  # Allow for small floating-point differences
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total:.2f}, 결제 금액: {amount:.2f}")

        payment_id = self.next_payment_id
        self.next_payment_id += 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = Order.STATUS_CONFIRMED  # Update order status to confirmed after payment
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

try:
    # Create an order
    items = [
        Item("Laptop", 1200, 1, 0),
        Item("Mouse", 25, 2, 0),
        Item("Keyboard", 75, 1, 0)
    ]
    order_manager.add_order(1, items, inventory)

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
    print(order_manager.get_order(1))

    # Cancel order
    order_manager.cancel_order(1)
    print("\nOrder 1 after cancellation:")
    print(order_manager.get_order(1))

    # Process payment
    payment = order_manager.process_payment(1, order_manager.get_order(1).total, "Credit Card")
    print(f"\nPayment processed: {payment}")

    # Get payment details
    payment = order_manager.get_payment(1)
    if payment:
        print(f"\nPayment details for order 1: {payment}")

except ValueError as e:
    print(f"\nError: {e}")