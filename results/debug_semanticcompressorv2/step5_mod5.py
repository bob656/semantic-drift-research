from typing import List, Optional
from dataclasses import dataclass

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

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        # 상품을 재고에 등록
        if item_name in self.items:
            raise ValueError(f"Item {item_name} already exists in inventory")
        self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)

    def get_stock(self, item_name: str) -> Optional[int]:
        # 현재 재고 수량 반환
        return self.items.get(item_name, None).stock if item_name in self.items else None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        # 재고 차감 (부족 시 ValueError)
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} does not exist in inventory")
        item = self.items[item_name]
        if item.stock < quantity:
            raise ValueError(f"Not enough stock for {item_name}: required {quantity}, available {item.stock}")
        item.stock -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = "PENDING"
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        # 할인 적용된 총 가격 계산
        total = sum(item.price * item.quantity for item in self.items)
        return total - (total * self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리 초기화
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        # 새로운 주문 생성 및 저장, 재고 차감
        for item in items:
            if item.name not in inventory.items or item.quantity > inventory.items[item.name].stock:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)
        new_order = Order(order_id, items, discount_percent=0.0)  # 초기 할인율은 0으로 설정
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회, 없으면 None 반환
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> bool:
        # 주문 상태를 PENDING에서 CONFIRMED로 전환
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            return True
        return False

    def ship_order(self, order_id: int) -> bool:
        # 주문 상태를 CONFIRMED에서 SHIPPED로 전환
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            return True
        return False

    def cancel_order(self, order_id: int) -> None:
        # 주문 상태를 PENDING 또는 CONFIRMED에서 CANCELLED로 전환
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def list_orders(self) -> List[Order]:
        # 모든 주문 목록 반환
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        # 주어진 order_id의 할인율을 적용합니다.
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> Optional[float]:
        # 주어진 order_id의 최종 금액을 반환합니다.
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        # 결제 처리
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if abs(amount - order.total) < 1e-6:  # 부동 소수점 오차를 고려한 비교
                payment_id = len(self.payments) + 1
                new_payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = new_payment
                order.status = "CONFIRMED"
                return new_payment
            else:
                raise ValueError("결제 금액이 주문 총액과 일치하지 않습니다")
        return None

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        # 결제 정보 조회, 없으면 None 반환
        return self.payments.get(payment_id)

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item('apple', 0.99, 10)
    inventory.add_item('banana', 0.59, 20)
    inventory.add_item('orange', 0.79, 15)

    # 주문 추가
    item1 = Item(name='apple', price=0.99, quantity=2, stock=10)
    item2 = Item(name='banana', price=0.59, quantity=3, stock=20)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name='orange', price=0.79, quantity=1, stock=15)
    manager.add_order(2, [item3], inventory)

    # 주문 조회
    order = manager.get_order(1)
    print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 결제 처리
    try:
        payment = manager.process_payment(1, 2.46, 'credit card')
        print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    except ValueError as e:
        print(e)

    # 주문 상태 전환
    manager.confirm_order(1)
    manager.ship_order(1)

    # 주문의 최종 금액 확인
    print(f"Order ID 1's total after discount and status change: {manager.get_order_total(1)}")

    # 주문 취소 시도
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 남아 있는 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")