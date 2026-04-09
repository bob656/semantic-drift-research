from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int = 0

class Inventory:
    def __init__(self):
        self.items: Dict[str, Item] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            print(f"Item {item_name} already exists.")
            return
        self.items[item_name] = Item(item_name, price, 0, stock)
        print(f"Item {item_name} added to inventory.")

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
            print(f"Stock reduced for {item_name}. Remaining stock: {item.stock}")
        else:
            raise ValueError("재고 부족")

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.now)

    def calculate_total(self) -> float:
        item_total = sum(item.price * item.quantity for item in self.items)
        return item_total - (item_total * self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}
        self.payments: Dict[int, Payment] = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return

        for item in items:
            stock = inventory.get_stock(item.name)
            if stock is None or stock < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")

        try:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)

            self.orders[order_id] = Order(order_id, items)
            print(f"Order {order_id} added.")
        except ValueError as e:
            print(e)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order {order_id} confirmed.")
        else:
            print(f"Order ID {order_id} not found or already confirmed.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order {order_id} shipped.")
        else:
            print(f"Order ID {order_id} not found or not confirmed.")

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order {order_id} cancelled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found or already shipped.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                print(f"Discount applied to Order {order_id}: {discount_percent * 100}%")
            else:
                print(f"Order ID {order_id} not found.")
        else:
            print("Invalid discount percentage. Please enter a value between 0 and 1.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def list_orders(self) -> List[Order]:
        return sorted([order for order in self.orders.values() if order.status != "CANCELLED"], key=lambda x: x.created_at)

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return sorted([order for order in self.orders.values() if order.status == status], key=lambda x: x.created_at)

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if not order:
            print(f"Order ID {order_id} not found.")
            return None

        if amount != order.total:
            raise ValueError("Amount does not match the order total.")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "PAID"
        print(f"Payment processed for Order {order_id}.")
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

# Example usage remains the same as before, but with added functionality.