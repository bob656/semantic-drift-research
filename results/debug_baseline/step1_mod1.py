from dataclasses import dataclass, field
from typing import List

@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1

class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items: List[Item]):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return
        self.orders[order_id] = Order(order_id, items)
        print(f"Order ID {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order ID {order_id} cancelled.")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [str(order) for order in self.orders.values()]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    item1 = Item(name="item1", price=5.25)
    item2 = Item(name="item2", price=5.25, quantity=2)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=2.50)
    manager.add_order(2, [item3])

    print("Order List:")
    for order in manager.list_orders():
        print(order)

    order = manager.get_order(1)
    if order:
        print(f"Order ID 1: {order.items}, Total: {order.total}")

    manager.cancel_order(2)
    print("After cancelling Order ID 2, Order List:")
    for order in manager.list_orders():
        print(order)