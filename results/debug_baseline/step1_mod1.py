from dataclasses import dataclass
from typing import List, Optional

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
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return
        self.orders[order_id] = Order(order_id, items)
        print(f"Order {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order {order_id} cancelled.")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    item1 = Item("item1", 25.0, 2)
    item2 = Item("item2", 10.0, 3)
    item3 = Item("item3", 20.0, 1)

    manager.add_order(1, [item1, item2])
    manager.add_order(2, [item3])

    print("Order List:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    order = manager.get_order(1)
    if order:
        print(f"\nRetrieved Order: Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")
    else:
        print("\nOrder not found.")

    manager.cancel_order(1)
    print("\nAfter cancelling Order 1:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")