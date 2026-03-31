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

    def __init__(self, order_id, items, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.status = status
        self.discount_percent = 0.0
        self.total = self.calculate_total()
        self.created_at = datetime.datetime.now()

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Status: {self.status}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Created At: {self.created_at}"


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
            raise ValueError(f"Item not found: {item_name}")
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
            print(f"Error adding order: {e}")
            return None

        order = Order(order_id, items)
        self.orders[order_id] = order
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            print(f"Error: Order with ID {order_id} not found.")
            return

        if order.status == Order.STATUS_SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            print(f"Error: Cannot cancel order {order_id} with status {order.status}")

    def list_orders(self):
        return [order for order in self.orders.values() if order.status not in (Order.STATUS_CANCELLED)]

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
            else:
                print("Error: Discount percent must be between 0.0 and 1.0")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CONFIRMED

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.next_payment_id += 1
        self.payments[order_id] = payment
        return payment

    def get_payment(self, order_id):
        return self.payments.get(order_id)

    def get_order_history(self):
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str):
        return [order for order in self.orders.values() if order.status == status]


# Example Usage
if __name__ == '__main__':
    inventory = Inventory()
    inventory.add_item("Laptop", 1200.00, 5)
    inventory.add_item("Mouse", 25.00, 10)
    inventory.add_item("Keyboard", 75.00, 7)

    order_manager = OrderManager(inventory)

    # Create an order
    items = [
        Item("Laptop", 1200.00, 1, 0),
        Item("Mouse", 25.00, 1, 0),
        Item("Keyboard", 75.00, 1, 0)
    ]
    order1 = order_manager.add_order(1, items, inventory)

    # Create another order
    items2 = [
        Item("Laptop", 1200.00, 1, 0)
    ]
    order2 = order_manager.add_order(2, items2, inventory)

    if order1:
        print(f"Order created: {order1}")
    if order2:
        print(f"Order created: {order2}")

    # List all orders
    print("\nAll Orders:")
    for order in order_manager.list_orders():
        print(order)

    # Apply discount to order 1
    order_manager.apply_discount(1, 0.1)  # 10% discount

    # List orders after discount
    print("\nOrders after discount:")
    for order in order_manager.list_orders():
        print(order)

    # Get total for order 2
    total = order_manager.get_order_total(1)
    if total:
        print(f"\nTotal for Order 1: {total:.2f}")

    # Confirm order 2
    order_manager.confirm_order(1)

    # Process payment for order 1
    try:
        payment = order_manager.process_payment(1, 1225.00, "Credit Card")
        if payment:
            print(f"\nPayment processed: {payment}")
    except ValueError as e:
        print(f"\nError processing payment: {e}")

    # Ship order 2
    order_manager.confirm_order(2)

    # Cancel order 1
    try:
        order_manager.cancel_order(1)
    except ValueError as e:
        print(f"\nError cancelling order 1: {e}")

    # List orders after cancellation
    print("\nOrders after cancellation:")
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

    print("\nCancelled Orders:")
    for order in order_manager.get_orders_by_status(Order.STATUS_CANCELLED