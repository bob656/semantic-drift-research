from dataclasses import dataclass, field
from typing import List, Optional
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 추가된 재고 필드

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    total: Optional[float] = None

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        if item_name in self.items:
            print(f"Item {item_name} already exists in inventory.")
        else:
            self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
            print(f"Item {item_name} added to inventory with stock {stock}.")

    def get_stock(self, item_name):
        return self.items.get(item_name).stock if item_name in self.items else 0

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} does not exist in inventory.")
        item = self.items[item_name]
        if item.stock >= quantity:
            item.stock -= quantity
            print(f"Stock for {item_name} reduced by {quantity}. Remaining stock: {item.stock}.")
        else:
            raise ValueError(f"Not enough stock for {item_name}: requested {quantity}, available {item.stock}.")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return

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
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def get_order_history(self):
        return sorted([order for order in self.orders.values()], key=lambda x: x.created_at)

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
            if amount != order.total:
                raise ValueError("결제 금액이 주문 총액과 일치하지 않습니다.")
            else:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} paid and confirmed.")
                return payment
        else:
            print("주문을 결제할 수 없습니다.")
            return None

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"Order ID {order_id}에 대한 결제 정보가 없습니다.")
        return None

    def get_orders_by_status(self, status: str):
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("item1", 25.0, 3)
    inventory.add_item("item2", 10.0, 5)
    inventory.add_item("item3", 20.0, 2)

    # 주문 추가 (재고 부족)
    manager.add_order(1, [Item("item1", 25.0, 4), Item("item2", 10.0, 1)], inventory)  # 재고 부족으로 실패

    # 주문 추가 성공
    manager.add_order(2, [Item("item1", 25.0, 3), Item("item2", 10.0, 1)], inventory)

    # 주문 상태 변경
    manager.confirm_order(2)
    manager.ship_order(2)

    # 취소 시도 (배송 중이므로 실패)
    try:
        manager.cancel_order(2)
    except ValueError as e:
        print(e)  # 배송 중인 주문은 취소할 수 없습니다

    # 주문 이력 조회
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 특정 상태의 주문 조회
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    print("Cancelled Orders:")
    for order in cancelled_orders:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 재고 조회
    print("Stock for item1:", inventory.get_stock("item1"))
    print("Stock for item2:", inventory.get_stock("item2"))