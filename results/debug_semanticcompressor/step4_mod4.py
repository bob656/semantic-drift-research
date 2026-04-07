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
        self.discount_percent = max(0.0, min(1.0, discount_percent))  # Ensure within range [0.0, 1.0]
        self.total = sum(item.price * item.quantity for item in items) * (1 - self.discount_percent)
        self.status = "PENDING"  # Initial status is PENDING

    def apply_discount(self, discount_percent: float):
        self.discount_percent = max(0.0, min(1.0, discount_percent))  # Ensure within range [0.0, 1.0]
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문 목록을 저장할 딕셔너리 초기화
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        # 새로운 주문 추가
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items, discount_percent)
            print(f"Order with ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        # 주문 취소 (상태만 변경)
        order = self.get_order(order_id)
        if order:
            if order.status in ["PENDING", "CONFIRMED"]:
                order.status = "CANCELLED"
                print(f"Order with ID {order_id} has been cancelled.")
            elif order.status == "SHIPPED":
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"No order found with ID {order_id}.")

    def confirm_order(self, order_id: int) -> None:
        # 주문 확인 (PENDING → CONFIRMED)
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order with ID {order_id} has been confirmed.")
        else:
            print(f"No pending order found with ID {order_id}.")

    def ship_order(self, order_id: int) -> None:
        # 주문 배송 (CONFIRMED → SHIPPED)
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order with ID {order_id} has been shipped.")
        else:
            print(f"No confirmed order found with ID {order_id}.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        # 주문에 할인 적용
        order = self.get_order(order_id)
        if order:
            order.apply_discount(discount_percent)
            print(f"Discount applied to Order ID {order_id}.")
        else:
            print(f"No order found with ID {order_id}.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        # 주문의 최종 금액 반환
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}.")
            return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        # 결제 처리
        order = self.get_order(order_id)
        if not order:
            print(f"No order found with ID {order_id}.")
            return None
        
        if order.total != amount:
            raise ValueError("Amount does not match the order total.")
        
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        
        # 결제 성공 시 Order status를 CONFIRMED로 변경
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        
        print(f"Payment processed for Order ID {order_id}.")
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        # 해당 주문의 결제 정보 반환
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

    def list_orders(self) -> List[Order]:
        # 모든 주문 목록 반환 (할인 적용 후 total 포함 및 상태 정보 포함)
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    manager.add_order(1, [Item("apple", 0.99, 2), Item("banana", 0.59, 3)], discount_percent=0.1)
    manager.add_order(2, [Item("orange", 1.49, 1)])

    print("Order 1:", [item.name for item in manager.get_order(1).items])  # ['apple', 'banana']
    print("Order 1 Total after discount:", manager.get_order_total(1))  # Should be less than original total

    manager.apply_discount(1, 0.2)
    print("Order 1 Total after additional 20% discount:", manager.get_order_total(1))

    payment = manager.process_payment(1, manager.get_order_total(1), "Credit Card")
    if payment:
        print(f"Payment ID: {payment.payment_id}, Method: {payment.method}")

    manager.confirm_order(1)
    manager.ship_order(1)

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)  # 배송 중인 주문은 취소할 수 없습니다

    print("List of orders with discounts applied and status:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}, Status: {order.status}")

    print("Payment details for Order 1:", manager.get_payment(1))

    print("List of orders after attempting to cancel shipped order 1 (should raise error):")
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)  # 배송 중인 주문은 취소할 수 없습니다

    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}, Status: {order.status}")