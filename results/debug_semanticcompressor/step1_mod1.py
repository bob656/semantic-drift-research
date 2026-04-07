from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        # 주문 목록을 저장할 딕셔너리 초기화
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        # 새로운 주문 추가
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items)
            print(f"Order with ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        # 주문 취소 (삭제)
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order with ID {order_id} has been cancelled.")
        else:
            print(f"No order found with ID {order_id}.")

    def list_orders(self) -> List[Order]:
        # 모든 주문 목록 반환
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    manager.add_order(1, [Item("apple", 0.99, 2), Item("banana", 0.59, 3)])
    manager.add_order(2, [Item("orange", 1.49, 1)])

    print("Order 1:", [item.name for item in manager.get_order(1).items])  # ['apple', 'banana']
    print("Order 2:", manager.get_order(2).total)  # 1.49

    manager.cancel_order(1)
    print("List of orders after cancelling order 1:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Total: {order.total}")