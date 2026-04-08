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
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        # 할인 적용된 총 가격 계산
        total = sum(item.price * item.quantity for item in self.items)
        return total - (total * self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리 초기화
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        # 새로운 주문 생성 및 저장
        new_order = Order(order_id, items, discount_percent)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        # 주문 조회, 없으면 None 반환
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> bool:
        # 주문 취소(삭제), 성공 여부를 boolean으로 반환
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def list_orders(self) -> List[Order]:
        # 모든 주문 목록 반환
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        # 주어진 order_id의 할인율을 적용합니다.
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()

    def get_order_total(self, order_id: int) -> Optional[float]:
        # 주어진 order_id의 최종 금액을 반환합니다.
        order = self.get_order(order_id)
        return order.total if order else None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name='apple', price=0.99, quantity=2)
    item2 = Item(name='banana', price=0.59, quantity=3)
    manager.add_order(1, [item1, item2], 0.1)  # 10% 할인

    item3 = Item(name='orange', price=0.79, quantity=1)
    manager.add_order(2, [item3])

    # 주문 조회
    order = manager.get_order(1)
    print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 할인 적용
    manager.apply_discount(1, 0.2)  # 20% 할인

    # 주문의 최종 금액 확인
    print(f"Order ID 1's total after discount: {manager.get_order_total(1)}")

    # 주문 취소
    success = manager.cancel_order(1)
    if success:
        print("Order cancelled successfully.")
    else:
        print("Failed to cancel order.")

    # 남아 있는 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")