from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 재고 추가

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name not in self.items:
            self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
        else:
            print(f"Item {item_name} already exists.")

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item {item_name} not found.")
            return None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
        else:
            raise ValueError("재고 부족")

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> float:
        return self._total

    @total.setter
    def total(self, value: float):
        self._total = value * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id not in self.orders:
            for item in items:
                try:
                    inventory.reduce_stock(item.name, item.quantity)
                except ValueError as e:
                    print(e)
                    return
            self.orders[order_id] = Order(order_id, items)
        else:
            print(f"Order ID {order_id} already exists.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order:
            if order.status in ["PENDING", "CONFIRMED"]:
                order.status = "CANCELLED"
            else:
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            print(f"Order ID {order_id} is not PENDING or does not exist.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            print(f"Order ID {order_id} is not CONFIRMED or does not exist.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
            else:
                print(f"Invalid discount percent {discount_percent}. Must be between 0.0 and 1.0.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def process_payment(self, payment_id: int, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if order and order.total == amount:
            order.status = "CONFIRMED"
            payment = Payment(payment_id=payment_id, order_id=order_id, amount=amount, method=method)
            self.payments[payment_id] = payment
            return payment
        else:
            raise ValueError("Payment amount does not match the total of the order or order not found.")

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_orders(self) -> List[Order]:
        return sorted([order for order in self.orders.values() if order.status != "CANCELLED"], key=lambda x: x.created_at)

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return sorted([order for order in self.orders.values() if order.status == status], key=lambda x: x.created_at)