from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            raise ValueError("Item already exists")
        new_item = Item(item_name, price, 0, stock)
        self.items[item_name] = new_item

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        if item is None:
            return None
        return item.stock

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if item is None:
            raise ValueError("Item does not exist")
        
        if item.stock >= quantity:
            item.stock -= quantity
        else:
            raise ValueError(f"재고 부족: {item.name}")

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = field(default="PENDING")
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        new_order = Order(order_id, items)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        order.discount_percent = discount_percent
        order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        return order.total

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError("주문 상태가 PENDING이 아닙니다")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError("주문 상태가 CONFIRMED가 아닙니다")

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if amount != order.total:
            raise ValueError("Payment amount must match the order total")
        
        payment_id = len(self.payments) + 1
        new_payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = new_payment
        
        order.status = "CONFIRMED"
        return new_payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda o: o.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("apple", 0.99, 10)
    inventory.add_item("banana", 0.59, 20)
    inventory.add_item("orange", 0.79, 15)

    # 주문 추가
    items1 = [Item("apple", 0.99, 2), Item("banana", 0.59, 3)]
    items2 = [Item("orange", 0.79, 1)]
    
    try:
        manager.add_order(1, items1, inventory)
        manager.add_order(2, items2, inventory)
    except ValueError as e:
        print(e)

    # 주문 조회
    order_1 = manager.get_order(1)
    if order_1:
        print(f"Order 1: {order_1.items[0].name} x {order_1.items[0].quantity}, "
              f"{order_1.items[1].name} x {order_1.items[1].quantity} - Total: ${order_1.total} - Status: {order_1.status}")

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후 주문 조회
    order_1 = manager.get_order(1)
    if order_1:
        print(f"Order 1 status after cancellation: {order_1.status}")

    # 주문 이력 조회
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, "
              f"Total: ${order.total} - Status: {order.status} - Created At: {order.created_at}")

    # 특정 상태의 주문 조회
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"Cancelled Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, "
              f"Total: ${order.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        if order:
            print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, "
                  f"Total: ${order.total} - Status: {order.status}")