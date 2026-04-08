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
        self.total = sum(item.price * item.quantity for item in items)
        self.discount_percent = discount_percent

    @property
    def total(self) -> float:
        return self._total

    @total.setter
    def total(self, value: float):
        self._total = value * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items, discount_percent)
        else:
            print(f"Order ID {order_id} already exists.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
            else:
                print(f"Invalid discount percent {discount_percent}. Must be between 0.0 and 1.0.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2)
    item2 = Item(name="item2", price=25.0, quantity=1)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=30.0, quantity=1)
    manager.add_order(2, [item3], discount_percent=0.1)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")

    # 할인 적용
    manager.apply_discount(2, 0.2)

    # 주문 총액 조회
    total = manager.get_order_total(2)
    if total is not None:
        print(f"Order 2 Total after discount: {total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")