from typing import List, Optional
from dataclasses import dataclass

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
    total: float = 0.0
    discount_percent: float = 0.0
    status: str = "PENDING"

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

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
        if item_name in self.items:
            raise ValueError(f"Item with name {item_name} already exists.")
        self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        return item.stock if item else None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if not item:
            raise ValueError(f"Item with name {item_name} does not exist.")
        if item.stock < quantity:
            raise ValueError("재고 부족")
        item.stock -= quantity

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order with ID {order_id} already exists.")
        
        for item in items:
            current_stock = inventory.get_stock(item.name)
            if not current_stock or current_stock < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)

        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        if self.orders[order_id].status != "PENDING":
            raise ValueError("Only PENDING orders can be confirmed.")
        self.orders[order_id].status = "CONFIRMED"

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        if self.orders[order_id].status != "CONFIRMED":
            raise ValueError("Only CONFIRMED orders can be shipped.")
        self.orders[order_id].status = "SHIPPED"

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        if self.orders[order_id].status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        if self.orders[order_id].status in ["PENDING", "CONFIRMED"]:
            self.orders[order_id].status = "CANCELLED"

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = sum(item.price * item.quantity for item in self.orders[order_id].items) * (1 - discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        order = self.get_order(order_id)
        if amount != order.total:
            raise ValueError("Payment amount must match the order total.")
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "CONFIRMED"
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 5.0, 10)
    inventory.add_item("item2", 3.25, 5)
    inventory.add_item("item3", 5.0, 8)

    manager = OrderManager()

    # 주문 추가
    item1 = Item(name="item1", price=5.0, quantity=2, stock=10)
    item2 = Item(name="item2", price=3.25, quantity=1, stock=5)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=5.0, quantity=1, stock=8)
    manager.add_order(2, [item3], inventory)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {', '.join(item.name for item in order.items)}, Total - {order.total}, Status - {order.status}")

    # 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join(item.name for item in order.items)}, Total - {order.total}, Status - {order.status}")

    # 결제 처리
    payment = manager.process_payment(1, 9.0, "Credit Card")
    if payment:
        print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")

    # 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join(item.name for item in order.items)}, Total - {order.total}, Status - {order.status}")

    # 결제 정보 조회
    payment_info = manager.get_payment(1)
    if payment_info:
        print(f"Payment ID: {payment_info.payment_id}, Order ID: {payment_info.order_id}, Amount: {payment_info.amount}, Method: {payment_info.method}")

    # 주문 확인
    manager.confirm_order(2)

    # 주문 배송
    manager.ship_order(2)

    # 취소 시도 (배송 중인 주문)
    try:
        manager.cancel_order(2)
    except ValueError as e:
        print(e)  # "배송 중인 주문은 취소할 수 없습니다"

    # 취소 시도 (PENDING 상태의 주문 추가 및 취소)
    manager.add_order(3, [item1], inventory)
    try:
        manager.cancel_order(3)
    except ValueError as e:
        print(e)

    # 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join(item.name for item in order.items)}, Total - {order.total}, Status - {order.status}")

    # 할인 적용
    manager.apply_discount(1, 0.2)

    # 할인된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join(item.name for item in order.items)}, Total - {order.total}, Status - {order.status}")