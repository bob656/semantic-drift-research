from typing import List, Optional
from dataclasses import dataclass
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 추가된 재고 필드

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # 환불 여부 필드 추가

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            raise ValueError(f"Item '{item_name}' already exists.")
        self.items[item_name] = {'price': price, 'stock': stock}

    def get_stock(self, item_name: str) -> Optional[int]:
        return self.items.get(item_name, {}).get('stock')

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items:
            raise ValueError(f"Item '{item_name}' does not exist.")
        
        current_stock = self.items[item_name]['stock']
        if quantity > current_stock:
            raise ValueError(f"재고 부족: {item_name}")
        
        self.items[item_name]['stock'] -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = "PENDING"  # 추가된 상태 필드
        self.created_at = datetime.datetime.now()  # 주문 생성 시각

    def apply_discount(self, discount_percent: float) -> None:
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order with ID {order_id} already exists.")
        
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError("주문 상태가 PENDING이 아닙니다")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError("주문 상태가 CONFIRMED이 아닙니다")

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        order.apply_discount(discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status != "CONFIRMED":
            raise ValueError("주문 상태가 CONFIRMED이 아닙니다")
        
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def refund_payment(self, order_id: int) -> None:
        payment = self.get_payment(order_id)
        if payment is None:
            raise ValueError(f"No payment found for Order ID {order_id}")
        
        if payment.refunded:
            raise ValueError("Payment already refunded")
        
        payment.refunded = True
        order = self.get_order(order_id)
        if order:
            order.status = "REFUNDED"

    def get_refunded_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status == "REFUNDED"]

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        valid_statuses = ["PENDING", "CONFIRMED", "SHIPPED", "CANCELLED", "REFUNDED"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Choose from {valid_statuses}")
        
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("item1", 25.0, 3)
    inventory.add_item("item2", 25.0, 4)
    inventory.add_item("item3", 20.0, 2)

    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2, stock=0)  # 재고는 Inventory에서 관리
    item2 = Item(name="item2", price=25.0, quantity=1, stock=0)
    manager.add_order(1, [item1, item2], inventory)

    item3 = Item(name="item3", price=20.0, quantity=1, stock=0)
    manager.add_order(2, [item3], inventory)

    # 주문 조회
    order_1 = manager.get_order(1)
    print(f"Order 1: {order_1.items}, Total: {order_1.total}, Status: {order_1.status}")

    # 모든 주문 목록 출력
    all_orders = manager.list_orders()
    for order in all_orders:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}, Status: {order.status}")

    # 결제 처리
    payment_1 = manager.process_payment(1, 75.0, "Credit Card")
    print(f"Payment for Order 1: Payment ID {payment_1.payment_id}, Amount: {payment_1.amount}, Method: {payment_1.method}")

    # 환불 처리
    try:
        manager.refund_payment(1)
    except ValueError as e:
        print(e)

    # 환불된 주문 조회
    refunded_orders = manager.get_refunded_orders()
    for order in refunded_orders:
        print(f"Refunded Order - Order ID: {order.order_id}, Total: {order.total}")

    # 주문 이력 조회
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order History - Order ID: {order.order_id}, Status: {order.status}, Created At: {order.created_at}")

    # 특정 상태의 주문 조회
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"CANCELLED Orders - Order ID: {order.order_id}, Total: {order.total}")