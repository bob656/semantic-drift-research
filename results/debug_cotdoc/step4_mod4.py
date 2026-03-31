from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.discount_percent: float = 0.0  # 할인율 필드 추가
        self.total = self.calculate_total()
        self.status: str = "PENDING"  # 주문 상태 추가

    def __repr__(self):
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, status={self.status})"

    def calculate_total(self) -> float:
        total = 0.0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)


class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}  # order_id를 키로 사용
        self.payments: Dict[int, Payment] = {}  # payment_id를 키로 사용

    def add_order(self, order_id: int, items: List[Item]) -> None:
        """주문 추가. order_id 중복 검사 수행."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        """주문 ID에 해당하는 주문 조회. 주문이 없으면 None 반환."""
        return self.orders.get(order_id)

    def list_orders(self) -> List[Order]:
        """모든 주문 목록 반환."""
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인율 적용."""
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> float:
        """주문 ID에 해당하는 주문의 최종 금액 반환."""
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def confirm_order(self, order_id: int) -> None:
        """주문 상태를 PENDING에서 CONFIRMED로 변경."""
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"

    def ship_order(self, order_id: int) -> None:
        """주문 상태를 CONFIRMED에서 SHIPPED로 변경."""
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"

    def cancel_order(self, order_id: int) -> None:
        """주문 상태를 CANCELLED로 변경. PENDING 또는 CONFIRMED 상태에서만 가능."""
        order = self.get_order(order_id)
        if not order:
            return  # 주문이 없으면 아무것도 하지 않음
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        if order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        """결제 처리."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found.")

        if abs(amount - order.total) > 0.001:  # 부동 소수점 비교를 위한 오차 허용
            raise ValueError(f"Payment amount {amount} does not match order total {order.total}.")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "CONFIRMED"
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        """해당 주문의 결제 정보 반환."""
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None


@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str


# 사용 예제
if __name__ == "__main__":
    # OrderManager 인스턴스 생성
    order_manager = OrderManager()

    # 주문 추가
    try:
        order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 20.0, 1)])
        order_manager.add_order(2, [Item("item3", 5.0, 10)])
    except ValueError as e:
        print(f"Error adding order: {e}")
        exit()

    # 주문 조회
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}, Status: {order.status}")

    # 주문 목록 확인
    orders = order_manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Total: {order.total}, Status: {order.status}")

    # 주문 확정
    order_manager.confirm_order(1)
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Status: {order.status}")

    # 배송
    order_manager.ship_order(1)
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Status: {order.status}")

    # 취소 시도
    try:
        order_manager.cancel_order(2)
    except ValueError as e:
        print(f"Error cancelling order: {e}")

    order = order_manager.get_order(2)
    if order:
        print(f"Order ID: {order.order_id}, Status: {order.status}")

    # 배송 중인 주문 취소 시도
    try:
        order_manager.cancel_order(1)
    except ValueError as e:
        print(f"Error cancelling order: {e}")

    # 결제 처리
    try:
        payment = order_manager.process_payment(1, order_manager.get_order(1).total, "credit_card")
        print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    except ValueError as e:
        print(f"Error processing payment: {e}")

    # 결제 정보 조회
    payment = order_manager.get_payment(1)
    if payment:
        print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")