from dataclasses import dataclass
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

@dataclass
class Order:
    order_id: int
    items: list[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"
    created_at: datetime = None  # 주문 생성 시각
    customer_id: int = None  # 고객 ID

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # 환불 여부

class Inventory:
    def __init__(self):
        self.items: dict[str, Item] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        """상품을 재고에 등록합니다."""
        if item_name in self.items:
            print(f"오류: 상품 {item_name}이 이미 존재합니다.")
            return
        new_item = Item(item_name, price, 1, stock)
        self.items[item_name] = new_item
        print(f"상품 {item_name}이 재고에 추가되었습니다.")

    def get_stock(self, item_name: str) -> int:
        """현재 재고 수량을 반환합니다."""
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"오류: 상품 {item_name}이 존재하지 않습니다.")
            return 0

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        """재고를 차감합니다. 부족 시 ValueError를 발생시킵니다."""
        item = self.items.get(item_name)
        if not item:
            raise ValueError(f"오류: 상품 {item_name}이 존재하지 않습니다.")
        if item.stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        item.stock -= quantity
        print(f"상품 {item_name} 재고가 {quantity}만큼 차감되었습니다.")

class Customer:
    def __init__(self, customer_id: int, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email

class OrderManager:
    def __init__(self):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}
        self.customers: dict[int, Customer] = {}

    def add_order(self, order_id: int, items: list[Item], inventory: Inventory, customer_id: int) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return

        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"오류: 고객 ID {customer_id}가 존재하지 않습니다.")

        total = sum(item.price * item.quantity for item in items)
        new_order = Order(order_id, items)
        new_order.total = total
        new_order.created_at = datetime.now()  # 주문 생성 시각 설정
        new_order.customer_id = customer_id
        self.orders[order_id] = new_order
        print(f"주문 {order_id}가 추가되었습니다.")

        # 재고 차감
        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                print(e)
                # 주문 취소 로직 구현 필요 (간단하게는 여기서 return)
                return

    def add_customer(self, customer_id: int, name: str, email: str) -> None:
        """고객을 등록합니다."""
        if customer_id in self.customers:
            print(f"오류: 고객 ID {customer_id}가 이미 존재합니다.")
            return
        new_customer = Customer(customer_id, name, email)
        self.customers[customer_id] = new_customer
        print(f"고객 {name}이 등록되었습니다.")

    def get_customer(self, customer_id: int) -> Customer | None:
        """고객 ID로 고객 정보를 조회합니다. 없으면 None을 반환합니다."""
        return self.customers.get(customer_id)

    def get_orders_by_customer(self, customer_id: int) -> list[Order]:
        """고객 ID로 고객의 모든 주문을 반환합니다."""
        orders_by_customer = []
        for order in self.orders.values():
            if order.customer_id == customer_id:
                orders_by_customer.append(order)
        return orders_by_customer

    def get_order(self, order_id: int) -> Order | None:
        """주문 ID로 주문을 조회합니다. 없으면 None을 반환합니다."""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """주문 ID로 주문을 취소합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return

        if order.status in ("SHIPPED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        if order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"주문 {order_id}가 취소되었습니다.")
        else:
            print(f"오류: 주문 ID {order_id}는 취소할 수 없는 상태입니다.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인을 적용합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return
        order.discount_percent = discount_percent
        order.total = order.total * (1 - discount_percent)
        print(f"주문 {order_id}에 {discount_percent * 100}% 할인이 적용되었습니다.")

    def get_order_total(self, order_id: int) -> float:
        """주문 총액을 반환합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return 0
        return order.total

    def confirm_order(self, order_id: int) -> None:
        """주문을 확정합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return
        order.status = "CONFIRMED"
        print(f"주문 {order_id}가 확정되었습니다.")

    def ship_order(self, order_id: int) -> None:
        """주문 배송 처리"""
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError(f"오류: 주문 ID {order_id}는 배송할 수 없는 상태입니다.")
        order.status = "SHIPPED"
        print(f"주문 ID {order_id}가 배송되었습니다.")

    def process_payment(self, order_id: int) -> None:
        """결제 처리"""
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError(f"오류: 주문 ID {order_id}는 이미 결제되었거나 취소/배송/환불된 상태입니다.")

        # 결제 정보 생성 (예시)
        payment_id

    def get_refunded_orders(self) -> list[Order]:
        """refund