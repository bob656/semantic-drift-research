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

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], total: float) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
            else:
                raise ValueError("Order ID does not exist")
        else:
            raise ValueError("Discount percent must be between 0.0 and 1.0")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            raise ValueError("Order ID does not exist")

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2)
    item2 = Item(name="item2", price=10.0, quantity=3)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=20.0, quantity=1)
    manager.add_order(2, [item3])

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 할인된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후의 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {', '.join([f'{item.name} (x{item.quantity})' for item in order.items])}, Total - {order.total}")