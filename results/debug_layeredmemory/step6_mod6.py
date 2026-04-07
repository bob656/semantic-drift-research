from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

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
            print(f"Item '{item_name}' already exists.")
        else:
            self.items[item_name] = Item(item_name, price, 0, stock)
            print(f"Item added to inventory: {item_name}")

    def get_stock(self, item_name: str) -> Optional[int]:
        # 현재 재고 수량 반환
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"No item found with name '{item_name}'.")
            return None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        # 재고 차감 (부족 시 ValueError)
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Stock reduced for {item_name}: New stock is {item.stock}")
        else:
            raise ValueError(f"Not enough stock for {item_name}. Current stock: {item.stock}")

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문 목록을 저장할 딕셔너리 초기화
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        # 새로운 주문 추가
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            try:
                for item in items:
                    inventory.reduce_stock(item.name, item.quantity)
                self.orders[order_id] = Order(order_id, items)
                print(f"Order added with ID {order_id}")
            except ValueError as e:
                print(e)

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        # 주문 확인 (결제 없이 수동으로)
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} has been confirmed.")
        else:
            print(f"No pending order found with ID {order_id}")

    def ship_order(self, order_id: int) -> None:
        # 주문 배송
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} has been shipped.")
        else:
            print(f"No confirmed order found with ID {order_id}")

    def cancel_order(self, order_id: int) -> None:
        # 주문 취소
        order = self.get_order(order_id)
        if order and order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order with ID {order_id} has been cancelled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"No order found with ID {order_id}")

    def list_orders(self) -> List[Order]:
        # 모든 활성 주문 목록 반환
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        # 할인 적용
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
                print(f"Discount applied to Order ID {order_id}. New total: {order.total}")
            else:
                print(f"No order found with ID {order_id}")
        else:
            print("Invalid discount percent. Please enter a value between 0.0 and 1.0.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        # 주문의 최종 금액 반환
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}")
            return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        # 결제 처리
        order = self.get_order(order_id)
        if not order:
            print(f"No order found with ID {order_id}.")
            return None
        
        if amount != order.total:
            raise ValueError("Amount does not match the order total.")
        
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        
        order.status = "CONFIRMED"
        print(f"Payment processed for Order ID {order_id}. Status changed to CONFIRMED.")
        
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        # 해당 주문의 결제 정보 반환
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order with ID {order_id}")
        return None

    def get_order_history(self) -> List[Order]:
        # 모든 주문 (CANCELLED 포함)을 생성 시각 기준으로 정렬하여 반환
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        # 지정한 상태의 주문만 반환
        valid_statuses = {"PENDING", "CONFIRMED", "SHIPPED", "CANCELLED"}
        if status not in valid_statuses:
            print(f"Invalid status. Choose from {valid_statuses}.")
            return []
        
        return [order for order in self.orders.values() if order.status == status]

# Example usage remains the same as provided