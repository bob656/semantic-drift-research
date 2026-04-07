from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 현재 재고 수량 추가

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
            print(f"Item {item_name} already exists.")
        else:
            self.items[item_name] = Item(item_name, price, 0, stock)
            print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name: str) -> Optional[int]:
        # 현재 재고 수량 반환
        item = self.items.get(item_name)
        return item.stock if item else None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        # 재고 차감 (부족 시 ValueError)
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Reduced stock of {item_name} by {quantity}.")
        else:
            raise ValueError(f"재고 부족: {item_name}")

@dataclass(order=True)
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)
    
    def apply_discount(self, discount_percent: float):
        self.discount_percent = max(0.0, min(1.0, discount_percent))  # Ensure within range [0.0, 1.0]
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
            for item in items:
                try:
                    inventory.reduce_stock(item.name, item.quantity)
                except ValueError as e:
                    print(e)
                    return
            self.orders[order_id] = Order(order_id, items)
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
        # 모든 활성 주문 목록 반환 (할인 적용 후 total 포함 및 상태 정보 포함)
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def get_order_history(self) -> List[Order]:
        # CANCELLED 포함 모든 주문을 생성 시각 기준으로 정렬하여 반환
        return sorted(self.orders.values(), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        # 지정한 상태의 주문만 반환
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("apple", 0.99, 10)
    inventory.add_item("banana", 0.59, 15)

    manager = OrderManager()
    manager.add_order(1, [Item("apple", 0.99, 2), Item("banana", 0.59, 3)], inventory)
    manager.add_order(2, [Item("orange", 1.49, 1)])

    print("Order 1:", [item.name for item in manager.get_order(1).items])  # ['apple', 'banana']
    print("Order 1 Total:", manager.get_order_total(1))  # Order 1 Total: 2.5700000000000003
    print("Order 2 Total:", manager.get_order_total(2))  # Order 2 Total: 1.49

    print("List of active orders with discounts applied and status:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}, Status: {order.status}")

    manager.cancel_order(1)
    print("\nAfter canceling Order 1, list of active orders:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}, Status: {order.status}")

    print("\nOrder history (all orders including cancelled):")
    for order in manager.get_order_history():
        print(f"Order ID: {order.order_id}, Created At: {order.created_at}, Total: {order.total}, Status: {order.status}")

    print("\nOrders by status 'CANCELLED':")
    for order in manager.get_orders_by_status("CANCELLED"):
        print(f"Order ID: {order.order_id}, Created At: {order.created_at}, Total: {order.total}, Status: {order.status}")