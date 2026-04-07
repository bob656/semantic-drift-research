from typing import List, Optional
from dataclasses import dataclass

# Item 클래스 추가
@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        # Order.total은 items의 price * quantity 합계로 자동 계산
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리, key는 order_id, value는 Order 객체
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items)
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order ID {order_id} canceled.")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=5.25, quantity=2)
    item2 = Item(name="item2", price=3.00, quantity=1)
    order_manager.add_order(1, [item1, item2])
    
    item3 = Item(name="item3", price=7.50, quantity=1)
    order_manager.add_order(2, [item3])
    
    # 주문 조회
    order = order_manager.get_order(1)
    if order:
        print(f"Order ID {order.order_id}: Items={order.items}, Total={order.total}")
    
    # 주문 취소
    order_manager.cancel_order(2)
    
    # 모든 주문 목록 출력
    for order in order_manager.list_orders():
        print(f"Order ID {order.order_id}: Items={order.items}, Total={order.total}")