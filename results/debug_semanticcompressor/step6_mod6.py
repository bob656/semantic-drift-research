from typing import Dict, List, Optional
from dataclasses import dataclass, field
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 추가된 필드

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Inventory:
    def __init__(self):
        self.items: Dict[str, Item] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            raise ValueError("Item already exists")
        new_item = Item(item_name, price, 0, stock)
        self.items[item_name] = new_item

    def get_stock(self, item_name: str) -> Optional[int]:
        return self.items.get(item_name, None).stock if item_name in self.items else None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items or self.items[item_name].stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name].quantity -= quantity
        self.items[item_name].stock -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0, status: str = "PENDING"):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = status
        self.created_at = datetime.datetime.now()  # created_at 필드 추가

    def apply_discount(self, discount_percent: float) -> None:
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("discount_percent must be between 0.0 and 1.0")
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

    def confirm_order(self):
        if self.status == "PENDING":
            self.status = "CONFIRMED"
        else:
            raise ValueError("Order must be PENDING to be confirmed")

    def ship_order(self):
        if self.status == "CONFIRMED":
            self.status = "SHIPPED"
        else:
            raise ValueError("Order must be CONFIRMED to be shipped")

class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}
        self.payments: Dict[int, Payment] = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        
        # 재고 확인 및 차감
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        new_order = Order(order_id, items)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == "PENDING" or order.status == "CONFIRMED":
            order.status = "CANCELLED"
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        self.orders[order_id].apply_discount(discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order does not exist")
        if amount != order.total:
            raise ValueError("Payment amount must match order total")

        payment_id = max(self.payments.keys(), default=0) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment

        order.confirm_order()
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def get_order_history(self) -> List[Order]:
        return list(self.orders.values())

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
order_manager = OrderManager()

inventory = Inventory()
inventory.add_item("apple", 0.5, 10)
inventory.add_item("banana", 0.3, 20)
inventory.add_item("cake", 4.0, 5)

order_manager.add_order(1, [Item("apple", 0.5, 2), Item("banana", 0.3, 3)], inventory=inventory)
order_manager.add_order(2, [Item("cake", 4.0, 1)], inventory=inventory)

print("All orders:")
for order in order_manager.list_orders():
    print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")

cancelled_order = order_manager.get_order(1)
if cancelled_order:
    try:
        cancelled_order.cancel_order()
        print(f"Cancelled Order: {[item.name for item in cancelled_order.items]}")
    except ValueError as e:
        print(e)

try:
    order_manager.apply_discount(2, discount_percent=0.3)
except ValueError as e:
    print(e)

print("\nRemaining orders:")
for order in order_manager.list_orders():
    print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")

payment = order_manager.process_payment(2, 4.0, "credit card")
print(f"\nProcessed Payment: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")

order_manager.get_order(2).confirm_order()
try:
    order_manager.get_order(2).ship_order()
except ValueError as e:
    print(e)

print("\nRemaining orders after shipping:")
for order in order_manager.list_orders():
    print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")

# 주문 이력 확인
print("\nOrder History:")
for order in order_manager.get_order_history():
    print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}, Created At: {order.created_at}")

# 특정 상태의 주문 확인
print("\nOrders by status 'PENDING':")
for order in order_manager.get_orders_by_status("PENDING"):
    print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")