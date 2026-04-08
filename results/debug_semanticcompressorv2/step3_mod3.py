from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = "PENDING"

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

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
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
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item("item1", 5.0, 2)
    item2 = Item("item2", 3.5, 3)
    manager.add_order(1, [item1, item2], discount_percent=0.1)

    item3 = Item("item3", 8.0, 1)
    item4 = Item("item4", 4.5, 2)
    manager.add_order(2, [item3, item4])

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")

    # 주문 확인
    order.confirm_order()
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")

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

    # 모든 주문 목록 출력
    orders = manager.list_orders()
    for o in orders:
        print(f"Order ID: {o.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in o.items]}, Total: {o.total}, Status: {o.status}")

    # 잘못된 상태의 주문 취소 시도
    try:
        order.cancel_order()
        order = manager.get_order(1)
        if order:
            print(f"Order ID: {order.order_id}, Items: {[f'{item.name} ({item.quantity})' for item in order.items]}, Total: {order.total}, Status: {order.status}")
    except ValueError as e:
        print(e)  # Order is not pending