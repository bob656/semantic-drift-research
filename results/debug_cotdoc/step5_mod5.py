from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 재고 수량 추가


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

    def add_order(self, order_id: int, items: List[Item], inventory: 'Inventory') -> None:
        """주문 추가. order_id 중복 검사 수행."""
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")

        for item in items:
            if inventory.get_stock(item.name) < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")
            inventory.reduce_stock(item.name, item.quantity)

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


class Inventory:
    def __init__(self):
        self.items: Dict[str, int] = {}  # item_name을 키로 사용

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        """상품을 재고에 등록."""
        self.items[item_name] = stock

    def get_stock(self, item_name: str) -> int:
        """현재 재고 수량 반환."""
        return self.items.get(item_name, 0)

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        """재고 차감 (부족 시 ValueError)."""
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} not found in inventory.")
        if self.items[item_name] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name] -= quantity


# 사용 예제
if __name__ == "__main__":
    # OrderManager 인스턴스 생성
    order_manager = OrderManager()

    # Inventory 인스턴스 생성
    inventory = Inventory()
    inventory.add_item("item1", 10.0, 100)
    inventory.add_item("item2", 20.0, 50)

    try:
        order_manager.add_order(1, [Item("item1", 10.0, 2, 0), Item("item2", 20.0, 3, 0)], inventory)
    except ValueError as e:
        print(f"Error: {e}")

    try:
        order_manager.add_order(2, [Item("item1", 10.0, 102, 0)], inventory)
    except ValueError as e:
        print(f"Error: {e}")

    print(inventory.get_stock("item1"))
    print(inventory.get_stock("item2"))