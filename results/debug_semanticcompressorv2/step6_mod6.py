from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

class Payment:
    def __init__(self, payment_id: int, order_id: int, amount: float, method: str):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.now)
    total: float = 0.0
    payments: List[Payment] = None

    def _calculate_total(self) -> None:
        total_before_discount = sum(item.price * item.quantity for item in self.items)
        self.total = total_before_discount * (1 - self.discount_percent)

class Inventory:
    def __init__(self):
        self.stock = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.stock:
            raise ValueError("Item already exists")
        self.stock[item_name] = {"price": price, "stock": stock}

    def get_stock(self, item_name: str) -> int:
        if item_name not in self.stock:
            raise ValueError("Item does not exist")
        return self.stock[item_name]["stock"]

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.stock or self.stock[item_name]["stock"] < quantity:
            raise ValueError(f"Insufficient stock for {item_name}")
        self.stock[item_name]["stock"] -= quantity

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payment_id_counter = 0

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        
        # 재고 확인 및 차감
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        new_order = Order(order_id, items)
        new_order._calculate_total()
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError("Only pending orders can be confirmed")

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError("Only confirmed orders can be shipped")

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
        else:
            raise ValueError("Only pending or confirmed orders can be cancelled")

    def get_order_total(self, order_id: int) -> float:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        return self.orders[order_id].total

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def get_payment(self, order_id: int) -> Optional[Payment]:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.payments is None or len(order.payments) == 0:
            return None
        return order.payments[-1]

    def get_order_history(self) -> List[Order]:
        return list(self.orders.values())

    def get_orders_by_status(self, status: str) -> List[Order]:
        if status not in ["PENDING", "CONFIRMED", "SHIPPED", "CANCELLED"]:
            raise ValueError("Invalid order status")
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    inventory = Inventory()

    # 재고 추가
    inventory.add_item("Apple", 0.5, 20)
    inventory.add_item("Banana", 0.3, 30)

    # 주문 추가
    items1 = [Item("Apple", 0.5, 2, 2), Item("Banana", 0.3, 3, 3)]
    manager.add_order(1, items1, inventory)
    
    items2 = [Item("Coffee", 2.0, 1, 1), Item("Tea", 1.5, 2, 2)]
    manager.add_order(2, items2, inventory)

    # 결제 처리
    payment1 = manager.process_payment(1, 3.4, "Credit Card")
    print(f"Payment ID: {payment1.payment_id}, Order ID: {payment1.order_id}, Amount: {payment1.amount}, Method: {payment1.method}")

    # 주문 확인
    order = manager.get_order(1)
    print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 결제 정보 조회
    payment_info = manager.get_payment(1)
    print(f"Payment ID: {payment_info.payment_id}, Order ID: {payment_info.order_id}, Amount: {payment_info.amount}, Method: {payment_info.method}")

    # 잘못된 상태에서의 취소 시도
    try:
        manager.cancel_order(2)
    except ValueError as e:
        print(e)

    # 배송 중인 주문 취소 시도
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 재고 부족 시 예외 발생
    try:
        items3 = [Item("Apple", 0.5, 10, 10), Item("Banana", 0.3, 20, 20)]
        manager.add_order(3, items3, inventory)
    except ValueError as e:
        print(e)

    # 주문 이력 확인
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 특정 상태의 주문 확인
    pending_orders = manager.get_orders_by_status("PENDING")
    print(f"Pending Orders:")
    for order in pending_orders:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: {order.total}, Status: {order.status}")