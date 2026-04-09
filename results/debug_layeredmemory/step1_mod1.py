from typing import List, Optional

class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        new_order = Order(order_id, items)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
        else:
            raise ValueError("Order ID does not exist")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    items1 = [Item("apple", 0.99, 2), Item("banana", 0.59, 3)]
    items2 = [Item("orange", 0.79, 1)]
    manager.add_order(1, items1)
    manager.add_order(2, items2)

    # 주문 조회
    order_1 = manager.get_order(1)
    print(f"Order 1: {order_1.items[0].name} x {order_1.items[0].quantity}, "
          f"{order_1.items[1].name} x {order_1.items[1].quantity} - Total: ${order_1.total}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, "
              f"Total: ${order.total}")

    # 주문 취소
    manager.cancel_order(1)
    
    # 취소된 후 주문 조회
    cancelled_order = manager.get_order(1)
    if cancelled_order is None:
        print("Order 1 has been cancelled.")