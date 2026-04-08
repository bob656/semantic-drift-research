from typing import List, Optional

class Order:
    def __init__(self, order_id: int, items: List[str], total: float):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[str], total: float) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        self.orders[order_id] = Order(order_id, items, total)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    manager.add_order(1, ["Apple", "Banana"], 2.5)
    manager.add_order(2, ["Bread", "Milk"], 3.0)
    
    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")
    
    # 모든 주문 목록 출력
    orders = manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")
    
    # 주문 취소
    manager.cancel_order(1)