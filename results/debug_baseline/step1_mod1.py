from dataclasses import dataclass, field
from typing import List

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

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

    print("\n주문 조회 (ID: 1):")
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name}({item.quantity})' for item in order.items]}, Total: {order.total}")
    else:
        print("주문을 찾을 수 없습니다.")

    print("\n주문 취소 (ID: 2):")
    if manager.cancel_order(2):
        print("주문이 취소되었습니다.")
    else:
        print("취소할 주문을 찾을 수 없습니다.")

    print("\n주문 목록 (취소 후):")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name}({item.quantity})' for item in order.items]}, Total: {order.total}")