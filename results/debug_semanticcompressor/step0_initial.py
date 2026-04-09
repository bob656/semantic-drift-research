from typing import List, Optional

class Order:
    def __init__(self, order_id: int, items: List[str], total: float):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리. 키는 order_id, 값은 Order 객체입니다.
        self.orders = {}

    def add_order(self, order_id: int, items: List[str], total: float) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            new_order = Order(order_id, items, total)
            self.orders[order_id] = new_order
            print(f"Order added with ID: {order_id}")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order with ID {order_id} cancelled.")
        else:
            print(f"No order found with ID {order_id}")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    manager.add_order(1, ["Apple", "Banana"], 5.99)
    manager.add_order(2, ["Cherry"], 3.49)

    # 주문 조회
    order_1 = manager.get_order(1)
    if order_1:
        print(f"Order 1: {order_1.items}, Total: ${order_1.total}")

    # 주문 취소
    manager.cancel_order(2)

    # 모든 주문 목록 출력
    all_orders = manager.list_orders()
    for order in all_orders:
        print(f"ID: {order.order_id}, Items: {order.items}, Total: ${order.total}")