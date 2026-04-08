from dataclasses import dataclass, field
from typing import List, Dict
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 현재 재고 수량

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        if item_name in self.items:
            print(f"Item {item_name} already exists. Updating stock.")
        self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
        print(f"Item {item_name} added to inventory with stock {stock}.")

    def get_stock(self, item_name):
        if item_name in self.items:
            return self.items[item_name].stock
        else:
            print(f"No such item: {item_name}")
            return None

    def reduce_stock(self, item_name, quantity):
        if item_name in self.items:
            item = self.items[item_name]
            if item.stock >= quantity:
                item.stock -= quantity
                print(f"Stock reduced for {item_name}. Remaining stock: {item.stock}")
            else:
                raise ValueError("재고 부족")
        else:
            print(f"No such item: {item_name}")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)
            total = sum(item.price * item.quantity for item in items) * (1 - 0.0)  # 기본 할인 없음
            order = Order(order_id=order_id, items=items, discount_percent=0.0, total=total)
            self.orders[order_id] = order
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print("Order cannot be confirmed.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print("Order cannot be shipped.")

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            # 재고 복구 로직 추가 필요
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
                print(f"Order ID {order_id} updated with discount {discount_percent*100}%.")
            else:
                print(f"Order ID {order_id} not found.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if abs(amount - order.total) < 1e-6:
                order.status = "CONFIRMED"
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = payment
                print(f"Order ID {order_id} paid successfully with {method}.")
                return payment
            else:
                raise ValueError("Payment amount does not match the total order cost.")
        else:
            print("Order cannot be processed for payment.")

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

    def get_order_history(self):
        sorted_orders = sorted(self.orders.values(), key=lambda o: o.created_at)
        return [order for order in sorted_orders]

    def get_orders_by_status(self, status: str) -> List['Order']:
        return [order for order in self.orders.values() if order.status == status]

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    total: float = field(init=False)
    status: str = "PENDING"
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    manager = OrderManager()

    # 재고 등록
    inventory.add_item("item1", 25.0, 3)
    inventory.add_item("item2", 10.0, 4)
    inventory.add_item("item3", 20.0, 2)

    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2, stock=inventory.get_stock("item1"))
    item2 = Item(name="item2", price=10.0, quantity=1, stock=inventory.get_stock("item2"))
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=20.0, quantity=1, stock=inventory.get_stock("item3"))
    manager.add_order(2, [item3], inventory)

    # 주문 이력 조회
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order ID: {order.order_id}, Created At: {order.created_at}, Status: {order.status}")

    # 특정 상태의 주문 조회
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"Cancelled Order ID: {order.order_id}, Created At: {order.created_at}")