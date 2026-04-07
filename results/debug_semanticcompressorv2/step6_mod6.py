from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

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

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        if item_name in self.items:
            print(f"Item {item_name} already exists.")
        else:
            self.items[item_name] = {'price': price, 'stock': stock}
            print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name):
        return self.items.get(item_name, {}).get('stock', 0)

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items:
            raise ValueError("Item not found in inventory.")
        elif self.items[item_name]['stock'] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        else:
            self.items[item_name]['stock'] -= quantity
            print(f"{quantity} units of {item_name} reduced from inventory.")

class Order:
    def __init__(self, order_id, items, discount_percent=0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = "PENDING"
        self.created_at = datetime.now()
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            for item in items:
                if inventory.get_stock(item.name) < item.quantity:
                    raise ValueError(f"재고 부족: {item.name}")
                inventory.reduce_stock(item.name, item.quantity)
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
            for item in order.items:
                inventory_item = next((i for i in items if i.name == item.name), None)
                if inventory_item:
                    inventory.reduce_stock(item.name, inventory_item.quantity)
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
            if order.total != amount:
                raise ValueError("결제 금액이 주문 총액과 일치하지 않습니다.")
            payment_id = len(self.payments) + 1
            payment = Payment(payment_id, order_id, amount, method)
            self.payments[payment.payment_id] = payment
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} paid and confirmed.")
            return payment
        else:
            print("결제할 수 없는 주문입니다.")
            return None

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"Order ID {order_id}의 결제 정보를 찾을 수 없습니다.")
        return None

    def get_order_history(self) -> List[Order]:
        return sorted(list(self.orders.values()), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        if status in ["PENDING", "CONFIRMED", "SHIPPED", "CANCELLED"]:
            return [order for order in self.orders.values() if order.status == status]
        else:
            print("Invalid status. Must be one of 'PENDING', 'CONFIRMED', 'SHIPPED', 'CANCELLED'")
            return []

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 추가
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 10.0, 5)
    inventory.add_item("item3", 20.0, 8)

    # 주문 추가
    item1 = Item("item1", 25.0, 2)
    item2 = Item("item2", 10.0, 1)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item("item3", 20.0, 1)
    manager.add_order(2, [item3], inventory)

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 결제 처리
    payment = manager.process_payment(1, 45.0, "Credit Card")
    if payment:
        print(f"Payment ID {payment.payment_id}: Order ID {payment.order_id}, Amount - {payment.amount}, Method - {payment.method}")

    # 주문 이력 조회
    all_orders = manager.get_order_history()
    for order in all_orders:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 특정 상태의 주문 조회
    pending_orders = manager.get_orders_by_status("PENDING")
    for order in pending_orders:
        print(f"Pending Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 주문 취소
    manager.cancel_order(1)