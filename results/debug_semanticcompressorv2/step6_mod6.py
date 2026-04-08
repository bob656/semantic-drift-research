from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

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
        if item_name in self.items:
            raise ValueError("Item already exists")
        self.items[item_name] = {"price": price, "stock": stock}

    def get_stock(self, item_name: str) -> int:
        return self.items.get(item_name, {}).get("stock", 0)

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items or self.items[item_name]["stock"] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name]["stock"] -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = "PENDING"
        self.payments = []
        self.created_at = datetime.now()

    def apply_discount(self, discount_percent: float) -> None:
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

    def confirm_order(self):
        if self.status == "PENDING":
            self.status = "CONFIRMED"
        else:
            raise ValueError("Order is not pending")

    def ship_order(self):
        if self.status == "CONFIRMED":
            self.status = "SHIPPED"
        else:
            raise ValueError("Order is not confirmed")

    def cancel_order(self):
        if self.status in ["PENDING", "CONFIRMED"]:
            self.status = "CANCELLED"
        elif self.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payment_id_counter = 1

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory, discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        self.orders[order_id] = Order(order_id, items, discount_percent)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        self.orders[order_id].apply_discount(discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order does not exist")
        if amount != order.total:
            raise ValueError("Payment amount must match the order total")
        
        payment = Payment(payment_id=self.payment_id_counter, order_id=order.order_id, amount=amount, method=method)
        self.orders[order_id].payments.append(payment)
        order.confirm_order()
        self.payment_id_counter += 1
        return payment

    def get_payment(self, order_id: int) -> Optional[List[Payment]]:
        order = self.get_order(order_id)
        if not order:
            return None
        return order.payments

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

    # 재고 등록
    inventory.add_item("item1", 5.0, 10)
    inventory.add_item("item2", 3.5, 15)

    # 주문 추가
    item1 = Item("item1", 5.0, 2, inventory.get_stock("item1"))
    item2 = Item("item2", 3.5, 3, inventory.get_stock("item2"))
    manager.add_order(1, [item1, item2], inventory, discount_percent=0.1)

    item3 = Item("item3", 8.0, 1, inventory.get_stock("item3"))
    item4 = Item("item4", 4.5, 2, inventory.get_stock("item4"))
    manager.add_order(2, [item3, item4], inventory)

    # 결제 처리
    payment = manager.process_payment(1, order.total, "Credit Card")
    print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")

    # 주문 확인
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 결제 정보 조회
    payments = manager.get_payment(1)
    if payments:
        for payment in payments:
            print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")

    # 주문 배송
    order.ship_order()
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 주문 취소
    try:
        order.cancel_order()
        order = manager.get_order(1)
        if order:
            print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")
    except ValueError as e:
        print(e)  # 배송 중인 주문은 취소할 수 없습니다

    # 잘못된 상태의 주문 취소 시도
    try:
        order.cancel_order()
        order = manager.get_order(1)
        if order:
            print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")
    except ValueError as e:
        print(e)  # Order is not pending

    # 주문 이력 조회
    history = manager.get_order_history()
    for order in history:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 특정 상태의 주문 조회
    pending_orders = manager.get_orders_by_status("PENDING")
    for order in pending_orders:
        print(f"Pending Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")