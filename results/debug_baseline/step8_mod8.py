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
class Customer:
    customer_id: int
    name: str
    email: str

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    total: float = field(init=False)
    created_at: datetime = field(default_factory=datetime.now)
    customer_id: int = None

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}
        self.customers = {}

    def add_customer(self, customer_id: int, name: str, email: str):
        if customer_id in self.customers:
            print(f"Customer ID {customer_id} already exists.")
        else:
            self.customers[customer_id] = Customer(customer_id, name, email)
            print(f"Customer ID {customer_id} added.")

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory, customer_id: int):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        elif customer_id not in self.customers:
            raise ValueError(f"Customer ID {customer_id} does not exist.")
        else:
            try:
                for item in items:
                    inventory.reduce_stock(item.name, item.quantity)
                self.orders[order_id] = Order(order_id, items, discount_percent=0.0, customer_id=customer_id)
                print(f"Order ID {order_id} added.")
            except ValueError as e:
                print(e)

    def get_order(self, order_id: int):
        return self.orders.get(order_id)

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
        return [f"Order ID: {order.order_id}, Customer ID: {order.customer_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values()]

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
            raise ValueError("Order does not exist.")
        
        payment = self.get_payment(order_id)
        if payment and not payment.refunded:
            payment.refunded = True
            print(f"Payment for Order ID {order_id} refunded.")
        else:
            raise ValueError("Payment already refunded or no payment found.")

    def get_order_history(self):
        return [f"Order ID: {order.order_id}, Customer ID: {order.customer_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values()]

    def get_orders_by_status(self, status: str):
        return [f"Order ID: {order.order_id}, Customer ID: {order.customer_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values() if order.status == status]

    def get_orders_by_customer(self, customer_id: int):
        return [f"Order ID: {order.order_id}, Status: {order.status}, Total: {order.total:.2f}" for order in self.orders.values() if order.customer_id == customer_id]

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 15.0, 5)
    manager = OrderManager()

    # 고객 등록
    manager.add_customer(1, "John Doe", "john.doe@example.com")
    manager.add_customer(2, "Jane Smith", "jane.smith@example.com")

    item1 = Item(name="item1", price=25.0)
    item2 = Item(name="item2", price=15.0)
    manager.add_order(1, [item1, item2], inventory, 1)

    item3 = Item(name="item3", price=20.0)
    manager.add_order(2, [item3], inventory, 2)

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

    print("\nOrders by Customer (Customer ID 1):")
    for order in manager.get_orders_by_customer(1):
        print(order)

    print("\nOrders by Status (CANCELLED):")
    for order in manager.get_orders_by_status("CANCELLED"):
        print(order)