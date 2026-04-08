from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id, items, discount_percent=0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = max(0.0, min(1.0, discount_percent))
        self.status = "PENDING"
        self.total = sum(item.price * item.quantity for item in items) * (1 - self.discount_percent)

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: List[Item], discount_percent=0.0):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return
        self.orders[order_id] = Order(order_id, items, discount_percent)
        print(f"Order ID {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print(f"Order ID {order_id} cannot be confirmed.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print(f"Order ID {order_id} cannot be shipped.")

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
            print(f"Order ID {order_id} cancelled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if order:
            order.discount_percent = max(0.0, min(1.0, discount_percent))
            order.total = sum(item.price * item.quantity for item in order.items) * (1 - order.discount_percent)
            print(f"Discount applied to Order ID {order_id}.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def list_orders(self):
        return [f"Order ID: {order.order_id}, Status: {order.status}, Total: {order.total:.2f}, Discount: {order.discount_percent*100}%" for order in self.orders.values()]

    def process_payment(self, order_id, amount, method) -> Payment:
        order = self.get_order(order_id)
        if not order or order.status != "PENDING":
            print(f"Order ID {order_id} is not pending.")
            return None
        if amount != order.total:
            raise ValueError("Amount does not match the total of the order.")
        
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        
        order.status = "CONFIRMED"
        print(f"Order ID {order_id} confirmed and paid with {method}.")
        
        return payment

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    item1 = Item(name="item1", price=5.25)
    item2 = Item(name="item2", price=5.25, quantity=2)
    manager.add_order(1, [item1, item2], 0.1)

    item3 = Item(name="item3", price=2.50)
    manager.add_order(2, [item3])

    print("Order List:")
    for order in manager.list_orders():
        print(order)

    order = manager.get_order(1)
    if order:
        print(f"Order ID 1: {order.items}, Total: {order.total:.2f}")

    try:
        payment = manager.process_payment(1, order.total, "Credit Card")
        print(f"Payment processed for Order ID 1 with Payment ID {payment.payment_id}.")
    except ValueError as e:
        print(e)

    payment_info = manager.get_payment(1)
    if payment_info:
        print(f"Payment Info for Order ID 1: {payment_info}")

    total = manager.get_order_total(2)
    if total is not None:
        print(f"Total for Order ID 2: {total:.2f}")

    try:
        manager.cancel_order(2)
    except ValueError as e:
        print(e)
    print("After cancelling Order ID 2, Order List:")
    for order in manager.list_orders():
        print(order)

    manager.confirm_order(1)
    manager.ship_order(1)
    print("After confirming and shipping Order ID 1, Order List:")
    for order in manager.list_orders():
        print(order)