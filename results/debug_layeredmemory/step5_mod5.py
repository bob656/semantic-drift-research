from typing import List, Optional
from dataclasses import dataclass

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

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)
        self.discount_percent = discount_percent
        self.status = "PENDING"  # 새로운 필드 추가

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
        return list(self.orders.values())

# 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 25.0, 5)
    inventory.add_item("item3", 30.0, 8)

    # 주문 추가 (재고 차감 확인)
    item1 = Item(name="item1", price=25.0, quantity=2, stock=10)
    item2 = Item(name="item2", price=25.0, quantity=1, stock=5)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=30.0, quantity=1, stock=8)
    manager.add_order(2, [item3], inventory)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 결제 처리
    try:
        payment = manager.process_payment(payment_id=1, order_id=1, amount=75.0, method="Credit Card")
        print(f"Payment processed: Payment ID - {payment.payment_id}, Order ID - {payment.order_id}, Amount - {payment.amount}, Method - {payment.method}")
    except ValueError as e:
        print(e)

    # 주문 배송
    manager.ship_order(1)

    # 할인 적용
    try:
        manager.apply_discount(2, 0.2)
    except ValueError as e:
        print(e)

    # 주문 총액 조회
    total = manager.get_order_total(2)
    if total is not None:
        print(f"Order 2 Total after discount: {total}")

    # 주문 취소 시도 (예외 처리)
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 결제 정보 조회
    payment = manager.get_payment(payment_id=1)
    if payment:
        print(f"Payment Info: Payment ID - {payment.payment_id}, Order ID - {payment.order_id}, Amount - {payment.amount}, Method - {payment.method}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")