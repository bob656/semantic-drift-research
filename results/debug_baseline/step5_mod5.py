from dataclasses import dataclass, field
from typing import List

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
            self.orders[order_id] = Order(order_id=order_id, items=items, discount_percent=0.0, total=total)
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
        return [(order.order_id, [f'{item.name} x{item.quantity}' for item in order.items], order.total, order.status) for order in self.orders.values()]

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

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 결제 처리
    try:
        payment = manager.process_payment(1, 45.0, "Credit Card")
    except ValueError as e:
        print(e)

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

    # 결제 정보 조회
    payment_info = manager.get_payment(1)
    if payment_info:
        print(f"Payment ID: {payment_info.payment_id}, Order ID: {payment_info.order_id}, Amount: {payment_info.amount}, Method: {payment_info.method}")

    # 모든 주문 목록
    all_orders = manager.list_orders()
    for order_id, items, total, status in all_orders:
        print(f"Order {order_id}: Items - {items}, Total - {total}, Status - {status}")

    # 특정 주문의 총액 확인
    print("Order 1 total:", manager.get_order_total(1))

    # 재고 확인
    print("Stock for item1:", inventory.get_stock("item1"))
    print("Stock for item2:", inventory.get_stock("item2"))
    print("Stock for item3:", inventory.get_stock("item3"))