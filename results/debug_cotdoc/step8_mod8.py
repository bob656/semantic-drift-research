from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 재고 수량 추가


class Order:
    def __init__(self, order_id: int, items: List[Item], customer_id: int):
        self.order_id = order_id
        self.items = items
        self.discount_percent: float = 0.0  # 할인율 필드 추가
        self.total = self.calculate_total()
        self.status: str = "PENDING"  # 주문 상태 추가
        self.created_at: datetime = datetime.datetime.now()  # 주문 생성 시각 추가
        self.customer_id = customer_id  # 고객 ID 추가

    def __repr__(self):
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, status={self.status}, customer_id={self.customer_id})"

    def calculate_total(self) -> float:
        total = 0.0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)


class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}  # order_id를 키로 사용
        self.payments: Dict[int, Payment] = {}  # payment_id를 키로 사용
        self.customers: Dict[int, Customer] = {}  # customer_id를 키로 사용

    def add_customer(self, customer_id: int, name: str, email: str) -> None:
        """고객 등록. customer_id 중복 검사 수행."""
        if customer_id in self.customers:
            raise ValueError(f"Customer ID {customer_id} already exists.")
        self.customers[customer_id] = Customer(customer_id, name, email)

    def get_customer(self, customer_id: int) -> Optional['Customer']:
        """고객 ID에 해당하는 고객 정보 조회. 고객이 없으면 None 반환."""
        return self.customers.get(customer_id)

    def add_order(self, order_id: int, items: List[Item], inventory: 'Inventory', customer_id: int) -> None:
        """주문 추가. order_id 중복 검사 수행."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")

        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found.")

        for item in items:
            if inventory.get_stock(item.name) < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)

        self.orders[order_id] = Order(order_id, items, customer_id)

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

    def get_order_history(self) -> List[Order]:
        """모든 주문 이력 반환 (CANCELLED 주문 포함), 생성 시간 순으로 정렬."""
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_customer(self, customer_id: int) -> List[Order]:
        """특정 고객의 모든 주문 반환."""
        orders = []
        for order in self.orders.values():
            if order.customer_id == customer_id:
                orders.append(order)
        return orders

    def get_orders_by_status(self, status: str) -> List[Order]:
        """특정 상태의 모든 주문 반환."""
        orders = []
        for order in self.orders.values():
            if order.status == status:
                orders.append(order)
        return orders

    def refund_payment(self, payment_id: int) -> None:
        """결제 환불."""
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found.")
        # 실제 환불 로직 구현 필요
        print(f"Refunded payment {payment_id}")

    def get_refunded_orders(self) -> List[Order]:
        """환불된 주문 목록 반환."""
        refunded_orders = []
        for order in self.orders.values():
            if order.status == "REFUNDED":
                refunded_orders.append(order)
        return refunded_orders


@dataclass
class Customer:
    customer_id: int
    name: str
    email: str


# 수정된 코드 테스트
if __name__ == '__main__':
    inventory = Inventory()
    order_manager = OrderManager()

    try:
        order_manager.add_customer(1, "John Doe", "john.doe@example.com")
        order_manager.add_order(1, [Item("item1", 10.0, 1, 0)], inventory, 1)
        order_manager.process_payment(1, 10.0, "credit")
    except ValueError as e:
        print(f"