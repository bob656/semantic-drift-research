from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = "PENDING"  # 주문 상태 추가
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], total: float) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order:
            if order.status in ("PENDING", "CONFIRMED"):
                order.status = "CANCELLED"
            else:
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            raise ValueError("Order ID does not exist")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order:
            if order.status == "PENDING":
                order.status = "CONFIRMED"
            else:
                raise ValueError("주문 상태가 PENDING이 아닙니다")
        else:
            raise ValueError("Order ID does not exist")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order:
            if order.status == "CONFIRMED":
                order.status = "SHIPPED"
            else:
                raise ValueError("주문 상태가 CONFIRMED이 아닙니다")
        else:
            raise ValueError("Order ID does not exist")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
            else:
                raise ValueError("Order ID does not exist")
        else:
            raise ValueError("Discount percent must be between 0.0 and 1.0")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            raise ValueError("Order ID does not exist")

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if order and amount == order.total:
            payment_id = len(self.payments) + 1
            payment = Payment(payment_id, order_id, amount, method)
            self.payments[payment_id] = payment
            order.status = "CONFIRMED"
            return payment
        else:
            raise ValueError("Order ID does not exist or the amount does not match the total")

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2)
    item2 = Item(name="item2", price=10.0, quantity=3)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=20.0, quantity=1)
    manager.add_order(2, [item3])

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 결제 처리
    try:
        payment = manager.process_payment(1, order.total, "CREDIT_CARD")
        print(f"Payment {payment.payment_id}: Order ID - {payment.order_id}, Amount - {payment.amount}, Method - {payment.method}")
    except ValueError as e:
        print(e)

    # 결제된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 결제 정보 조회
    payment = manager.get_payment(1)
    if payment:
        print(f"Payment {payment.payment_id}: Order ID - {payment.order_id}, Amount - {payment.amount}, Method - {payment.method}")

    # 주문 확인
    manager.confirm_order(2)

    # 확인된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 배송 처리
    manager.ship_order(1)

    # 배송 중인 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 할인 적용
    try:
        manager.apply_discount(1, 0.1)
    except ValueError as e:
        print(e)

    # 할인된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 주문 취소 시도
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 취소된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Status - {order.status}, Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")