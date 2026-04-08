from dataclasses import dataclass, field
from typing import List

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        return sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> bool:
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items)
            return True
        return False

    def get_order(self, order_id: int):
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def apply_discount(self, order_id: int, discount_percent: float) -> bool:
        if 0.0 <= discount_percent <= 1.0 and order_id in self.orders:
            self.orders[order_id].discount_percent = discount_percent
            self.orders[order_id].total = self.orders[order_id].calculate_total()
            return True
        return False

    def get_order_total(self, order_id: int) -> float:
        if order_id in self.orders:
            return self.orders[order_id].total
        return None

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    item1 = Item(name="item1", price=25.0, quantity=2)
    item2 = Item(name="item2", price=25.0)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=30.0)
    manager.add_order(2, [item3])

    print("주문 목록:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name}({item.quantity})' for item in order.items]}, Total: {order.total}")

    print("\n할인 적용 (ID: 1, 10% 할인):")
    if manager.apply_discount(1, 0.1):
        print("할인이 적용되었습니다.")
    else:
        print("할인을 적용할 수 없습니다.")

    print("\n주문 목록 (할인 후):")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name}({item.quantity})' for item in order.items]}, Total: {order.total}")

    print("\n주문 조회 (ID: 1, 최종 금액):")
    total = manager.get_order_total(1)
    if total is not None:
        print(f"Order ID: 1, Total: {total}")
    else:
        print("주문을 찾을 수 없습니다.")