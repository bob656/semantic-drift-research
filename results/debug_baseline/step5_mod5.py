from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1
    stock: int = 0

class OrderStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int):
        if item_name in self.items:
            raise ValueError(f"Item {item_name} already exists")
        self.items[item_name] = Item(item_name, price, quantity=0, stock=stock)

    def get_stock(self, item_name: str) -> Optional[int]:
        return self.items.get(item_name)?.stock

    def reduce_stock(self, item_name: str, quantity: int):
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} does not exist")
        if self.items[item_name].stock < quantity:
            raise ValueError(f"Not enough stock for {item_name}")
        self.items[item_name].stock -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = OrderStatus.PENDING

    def apply_discount(self, discount_percent: float):
        if 0 <= discount_percent <= 1:
            self.discount_percent = discount_percent
            self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)
        else:
            raise ValueError("discount percent must be between 0.0 and 1.0")

    def confirm_order(self):
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
        else:
            raise ValueError("Order status must be PENDING to be confirmed")

    def ship_order(self):
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.SHIPPED
        else:
            raise ValueError("Order status must be CONFIRMED to be shipped")

    def cancel_order(self):
        if self.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            self.status = OrderStatus.CANCELLED
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> bool:
        for item in items:
            if item.name not in inventory.items or inventory.items[item.name].stock < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items)
            return True
        return False

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int):
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
                order.status = OrderStatus.CANCELLED
            else:
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            raise KeyError("Order not found")

    def apply_discount(self, order_id: int, discount_percent: float):
        if order_id in self.orders:
            self.orders[order_id].apply_discount(discount_percent)
        else:
            raise KeyError("Order not found")

    def get_order_total(self, order_id: int) -> Optional[float]:
        return self.orders.get(order_id)?.total

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values()]

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        if order_id not in self.orders:
            raise KeyError("Order not found")

        order = self.orders[order_id]
        if amount != order.total:
            raise ValueError("Payment amount does not match order total")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment

        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED

        return payment

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

# 간단한 사용 예제
inventory = Inventory()
inventory.add_item("apple", 0.5, 100)
inventory.add_item("banana", 0.3, 50)
inventory.add_item("steak", 10.0, 20)
inventory.add_item("potatoes", 1.5, 75)

order_manager = OrderManager()
order_manager.add_order(1, [Item("apple", 0.5), Item("banana", 0.3)], inventory)
order_manager.add_order(2, [Item("steak", 10.0), Item("potatoes", 1.5)], inventory)

print(order_manager.get_order(1))
print(order_manager.list_orders())

payment = order_manager.process_payment(1, amount=4.95, method="Credit Card")
print(payment)
print(order_manager.get_order(1))

order_manager.get_order(1).ship_order()
print(order_manager.list_orders())

try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(e)

try:
    order_manager.cancel_order(2)
except ValueError as e:
    print(e)