from typing import List, Optional
from dataclasses import dataclass

# Item 클래스 추가
@dataclass
class Item:
    name: str
    price: float
    quantity: int

# Payment 클래스 추가
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
        # Order.total은 items의 price * quantity 합계에서 할인을 적용한 최종 금액으로 계산
        self.update_total()

    def update_total(self) -> None:
        subtotal = sum(item.price * item.quantity for item in self.items)
        self.total = subtotal - (subtotal * self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리, key는 order_id, value는 Order 객체
        self.orders = {}
        # 결제 정보를 저장할 딕셔너리, key는 payment_id, value는 Payment 객체
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items, discount_percent)
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print(f"Order ID {order_id} cannot be confirmed.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print(f"Order ID {order_id} cannot be shipped.")

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
                order.update_total()
                print(f"Order ID {order_id} updated with discount {discount_percent * 100}%.")
            else:
                print("Invalid discount percent. It should be between 0.0 and 1.0.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if amount == order.total:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id=payment_id, order_id=order_id, amount=amount, method=method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} processed with {method}.")
                return payment
            else:
                raise ValueError("Amount does not match the total order amount.")
        else:
            print(f"Order ID {order_id} cannot be processed for payment.")
            return None

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=5.25, quantity=2)
    item2 = Item(name="item2", price=3.00, quantity=1)
    order_manager.add_order(1, [item1, item2])
    
    item3 = Item(name="item3", price=7.50, quantity=1)
    order_manager.add_order(2, [item3], discount_percent=0.1)  # 10% 할인
    
    # 주문 조회
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID {order.order_id}: Items={order.items}, Total={order.total}, Status={order.status}")
    
    # 결제 처리
    try:
        payment = order_manager.process_payment(1, 13.50, "Credit Card")
        if payment:
            print(f"Payment ID {payment.payment_id} processed for Order ID {payment.order_id}.")
    except ValueError as e:
        print(e)
    
    # 주문 상태 변경
    order_manager.confirm_order(2)  # 수동으로 확인
    
    # 할인 적용
    try:
        order_manager.apply_discount(2, 0.2)  # 20% 할인
    except ValueError as e:
        print(e)
    
    # 주문 총액 조회
    total = order_manager.get_order_total(2)
    if total is not None:
        print(f"Order ID 2 Total after discount: {total}")
    
    # 취소 시도 (배송 중인 주문 취소 시도 예외 처리)
    try:
        order_manager.cancel_order(1)  # 이미 배송된 주문은 취소할 수 없음
    except ValueError as e:
        print(e)
    
    # 결제 정보 조회
    payment = order_manager.get_payment(1)
    if payment:
        print(f"Payment ID {payment.payment_id}: Order ID={payment.order_id}, Amount={payment.amount}, Method={payment.method}")
    
    # 모든 주문 목록 출력
    for order in order_manager.list_orders():
        print(f"Order ID {order.order_id}: Items={order.items}, Total={order.total}, Status={order.status}")