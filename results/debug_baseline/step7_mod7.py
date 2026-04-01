from dataclasses import dataclass
from typing import List
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # Added stock attribute


@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # Added refunded attribute


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REFUNDED = "REFUNDED"  # Added REFUNDED status

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()
        self.created_at = datetime.datetime.now()  # Added created_at

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}, Created At: {self.created_at}"

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
        # Return only active orders (PENDING, CONFIRMED, SHIPPED)
        return [order for order in self.orders.values() if order.status not in (Order.STATUS_CANCELLED, Order.STATUS_REFUNDED)]

    def get_order_history(self):
        # Return all orders, including cancelled ones, sorted by created_at
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str):
        # Return orders with the specified status
        return [order for order in self.orders.values() if order.status == status]

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
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        return order.total

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        order.status = Order.STATUS_CONFIRMED

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        if order.status != Order.STATUS_CONFIRMED:
            raise ValueError(f"Order must be confirmed before shipping.")
        order.status = Order.STATUS_SHIPPED

    def refund_payment(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        if order.status == Order.STATUS_REFUNDED:
            raise ValueError(f"Payment for order {order_id} has already been refunded.")

        payment = None
        for payment_id, p in self.payments.items():
            if p["order_id"] == order_id:
                payment = p
                break

        if not payment:
            raise ValueError(f"No payment found for order {order_id}.")

        payment["refunded"] = True
        order.status = Order.STATUS_REFUNDED

    def get_refunded_orders(self):
        refunded_orders = []
        for order_id, order in self.orders.items():
            payment = None
            for payment_id, p in self.payments.items():
                if p["order_id"] == order_id and p["refunded"]:
                    payment = p
                    break
            if payment:
                refunded_orders.append(order)
        return refunded_orders

    def process_payment(self, order_id, amount, payment_method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")
        if order.status == Order.STATUS_REFUNDED:
            raise ValueError(f"Cannot process payment for a refunded order.")

        if order.total != amount:
            raise ValueError(f"Payment amount does not match order total.")

        payment = {
            "payment_id": self.next_payment_id,
            "order_id": order_id,
            "amount": amount,
            "method": payment_method,
            "refunded": False
        }
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
    order_manager.add_order