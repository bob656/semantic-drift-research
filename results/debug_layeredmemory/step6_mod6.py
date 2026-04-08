from dataclasses import dataclass, field
from typing import List, Optional
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

@dataclass(order=True)
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    total: float = field(init=False)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        if item_name in self.items:
            print(f"Item {item_name} already exists.")
        else:
            self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
            print(f"Item {item_name} added.")

    def get_stock(self, item_name):
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item {item_name} not found.")
            return None

    def reduce_stock(self, item_name, quantity):
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Stock reduced by {quantity} for {item_name}.")
        else:
            raise ValueError("재고 부족")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            for item in items:
                try:
                    inventory.reduce_stock(item.name, item.quantity)
                except ValueError as e:
                    print(e)
                    return
            self.orders[order_id] = Order(order_id, items)
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
            # 재고 회복 로직 추가 필요
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def get_order_history(self):
        return sorted(self.orders.values(), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str):
        return [order for order in self.orders.values() if order.status == status]

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
            if order.total != amount:
                raise ValueError("Payment amount does not match the order total.")
            else:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} processed with payment ID {payment_id}.")
                return payment
        else:
            print("Payment cannot be processed.")
            return None

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("item1", 25.0, 5)
    inventory.add_item("item2", 10.0, 3)
    inventory.add_item("item3", 20.0, 2)

    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2, stock=0)
    item2 = Item(name="item2", price=10.0, quantity=1, stock=0)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=20.0, quantity=1, stock=0)
    manager.add_order(2, [item3], inventory)

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 결제 처리
    payment = manager.process_payment(1, manager.get_order_total(1), "credit card")
    if payment:
        print(f"Payment ID {payment.payment_id} processed for Order ID {payment.order_id}.")

    # 주문 상태 변경
    manager.confirm_order(1)
    manager.ship_order(1)

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 주문 조회 및 총액 확인
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 모든 주문 목록
    all_orders = manager.list_orders()
    for order in all_orders:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 취소된 주문 이력
    cancelled_orders = manager.get_order_history()
    for order in cancelled_orders:
        print(f"Order History: Order ID {order.order_id}, Created At {order.created_at}, Status - {order.status}")

    # 특정 상태의 주문
    pending_orders = manager.get_orders_by_status("PENDING")
    for order in pending_orders:
        print(f"Pending Orders: Order ID {order.order_id}, Total - {order.total}")

    # 취소된 주문 이력 (상태별로)
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"CANCELLED Orders: Order ID {order.order_id}, Created At {order.created_at}")