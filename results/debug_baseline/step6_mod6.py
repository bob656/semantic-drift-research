from dataclasses import dataclass, field
from typing import List, Optional
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int = 0

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
    status: str = field(default="PENDING", init=False)
    total: float = field(init=False)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now, init=False)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        if item_name in self.items:
            print(f"Item {item_name} already exists in inventory.")
        else:
            self.items[item_name] = Item(item_name, price, 0, stock)
            print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name):
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item {item_name} not found in inventory.")
            return None

    def reduce_stock(self, item_name, quantity):
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Stock for {item_name} reduced by {quantity}. Remaining: {item.stock}")
        else:
            raise ValueError("재고 부족")

class OrderManager:
    def __init__(self, inventory: Inventory):
        self.orders = {}
        self.payments = {}
        self.inventory = inventory

    def add_order(self, order_id, items: List[Item]):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            for item in items:
                if item.stock < item.quantity:
                    raise ValueError(f"재고 부족: {item.name}")
                self.inventory.reduce_stock(item.name, item.quantity)
            self.orders[order_id] = Order(order_id, items, discount_percent=0.0)
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
            for item in order.items:
                self.inventory.reduce_stock(item.name, -item.quantity)  # 재고 복원
            order.status = "CANCELLED"
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [(order.order_id, [f'{item.name} x{item.quantity}' for item in order.items], order.total, order.status) for order in self.orders.values() if order.status != "CANCELLED"]

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
            if amount == order.total:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} confirmed and paid.")
                return payment
            else:
                raise ValueError("Payment amount does not match the order total.")
        else:
            print("Order cannot be processed for payment.")

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"Payment for Order ID {order_id} not found.")
        return None

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda o: o.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    manager = OrderManager(inventory)

    # 상품 재고 등록
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 10.0, 5)

    item1 = Item("item1", 25.0, 2)
    item2 = Item("item2", 10.0, 3)

    # 주문 추가
    try:
        manager.add_order(1, [item1, item2])
    except ValueError as e:
        print(e)

    item3 = Item("item3", 20.0, 1)
    inventory.add_item("item3", 20.0, 5)
    try:
        manager.add_order(2, [item3])
    except ValueError as e:
        print(e)

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 결제 처리
    try:
        payment = manager.process_payment(1, 58.0, "Credit Card")
        print(f"Payment ID {payment.payment_id} processed for Order ID {payment.order_id}.")
    except ValueError as e:
        print(e)

    # 주문 상태 변경
    manager.confirm_order(2)  # 수동 확인

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 모든 주문 목록 (활성 주문만)
    all_orders = manager.list_orders()
    for order_id, items, total, status in all_orders:
        print(f"Order {order_id}: Items - {items}, Total - {total}, Status - {status}")

    # 주문 이력
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order {order.order_id}: Created at - {order.created_at}, Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 특정 상태의 주문
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"Cancelled Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Created at - {order.created_at}")

    # 결제 정보 조회
    payment = manager.get_payment(1)
    if payment:
        print(f"Payment ID {payment.payment_id} for Order ID {payment.order_id}: Amount - {payment.amount}, Method - {payment.method}")

    # 특정 주문의 총액 확인
    print("Order 1 total:", manager.get_order_total(1))

    # 재고 수량 조회
    print("Stock for item1:", inventory.get_stock("item1"))
    print("Stock for item2:", inventory.get_stock("item2"))