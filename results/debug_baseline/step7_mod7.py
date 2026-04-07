from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1
    stock: int = 0

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int):
        if item_name in self.items:
            print(f"Item {item_name} already exists.")
        else:
            self.items[item_name] = Item(name=item_name, price=price, quantity=1, stock=stock)
            print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name: str) -> int:
        if item_name in self.items:
            return self.items[item_name].stock
        else:
            print(f"Item {item_name} not found.")
            return 0

    def reduce_stock(self, item_name: str, quantity: int):
        if item_name in self.items:
            if self.items[item_name].stock >= quantity:
                self.items[item_name].stock -= quantity
                print(f"Stock reduced for {item_name}. Remaining stock: {self.items[item_name].stock}")
            else:
                raise ValueError(f"Not enough stock for {item_name}.")
        else:
            print(f"Item {item_name} not found.")

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    total: float = field(init=False)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            try:
                for item in items:
                    inventory.reduce_stock(item.name, item.quantity)
                self.orders[order_id] = Order(order_id, items, discount_percent=0.0)
                print(f"Order ID {order_id} added.")
            except ValueError as e:
                print(e)

    def get_order(self, order_id: int):
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int):
        if order_id in self.orders:
            if self.orders[order_id].status == "PENDING":
                self.orders[order_id].status = "CONFIRMED"
                print(f"Order ID {order_id} confirmed.")
            else:
                print(f"Order ID {order_id} is not in PENDING status.")
        else:
            print(f"Order ID {order_id} not found.")

    def ship_order(self, order_id: int):
        if order_id in self.orders:
            if self.orders[order_id].status == "CONFIRMED":
                self.orders[order_id].status = "SHIPPED"
                print(f"Order ID {order_id} shipped.")
            else:
                print(f"Order ID {order_id} is not in CONFIRMED status.")
        else:
            print(f"Order ID {order_id} not found.")

    def cancel_order(self, order_id: int):
        if order_id in self.orders:
            if self.orders[order_id].status in ["PENDING", "CONFIRMED"]:
                self.orders[order_id].status = "CANCELLED"
                print(f"Order ID {order_id} canceled.")
            elif self.orders[order_id].status == "SHIPPED":
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id: int, discount_percent: float):
        if 0.0 <= discount_percent <= 1.0:
            if order_id in self.orders:
                self.orders[order_id].discount_percent = discount_percent
                self.orders[order_id].total = sum(item.price * item.quantity for item in self.orders[order_id].items) * (1 - discount_percent)
                print(f"Discount applied to Order ID {order_id}.")
            else:
                print(f"Order ID {order_id} not found.")
        else:
            print("Invalid discount percentage. Please enter a value between 0.0 and 1.0.")

    def get_order_total(self, order_id: int):
        if order_id in self.orders:
            return self.orders[order_id].total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def list_orders(self):
        return [f"Order ID: {order.order_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values()]

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        if order_id not in self.orders:
            print(f"Order ID {order_id} not found.")
            return None

        order = self.orders[order_id]
        if order.total != amount:
            raise ValueError("Amount does not match the total of the order.")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment

        order.status = "CONFIRMED"
        print(f"Order ID {order_id} confirmed via payment.")
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

    def refund_payment(self, order_id: int):
        if order_id not in self.orders:
            print(f"Order ID {order_id} not found.")
            return

        order = self.orders[order_id]
        payment = self.get_payment(order_id)
        if payment and not payment.refunded:
            payment.refunded = True
            order.status = "REFUNDED"
            print(f"Payment for Order ID {order_id} refunded.")
        else:
            raise ValueError("Payment already refunded or no payment found.")

    def get_refunded_orders(self):
        return [f"Order ID: {order.order_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values() if self.get_payment(order.order_id) and self.get_payment(order.order_id).refunded]

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 15.0, 5)
    manager = OrderManager()

    item1 = Item(name="item1", price=25.0)
    item2 = Item(name="item2", price=15.0)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=20.0)
    manager.add_order(2, [item3], inventory)

    print("Order List:")
    for order in manager.list_orders():
        print(order)

    print("\nGet Order ID 1 total:")
    print(manager.get_order_total(1))

    try:
        payment = manager.process_payment(1, 65.0, "Credit Card")
        if payment:
            print(f"Payment processed: Payment ID {payment.payment_id}, Method: {payment.method}")
    except ValueError as e:
        print(e)

    print("\nAfter processing payment for Order ID 1:")
    print(manager.list_orders())

    manager.confirm_order(2)
    print("\nOrder ID 2 confirmed manually:")
    print(manager.list_orders())

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    print("\nAfter trying to cancel shipped order (Order ID 1):")
    print(manager.list_orders())

    manager.cancel_order(2)
    print("\nAfter canceling Order ID 2:")
    print(manager.list_orders())

    try:
        manager.refund_payment(1)
    except ValueError as e:
        print(e)

    print("\nAfter refunding payment for Order ID 1:")
    print(manager.list_orders())

    print("\nRefunded Orders:")
    for order in manager.get_refunded_orders():
        print(order)

    print("\nOrders by Status (CANCELLED):")
    for order in manager.get_orders_by_status("CANCELLED"):
        print(order)