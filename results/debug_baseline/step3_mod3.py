from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0, status: str = "PENDING"):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        item_total = sum(item.price * item.quantity for item in self.items)
        return item_total - (item_total * self.discount_percent)

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

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order {order_id} confirmed.")
        else:
            print(f"Order ID {order_id} not found or already confirmed.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order {order_id} shipped.")
        else:
            print(f"Order ID {order_id} not found or not confirmed.")

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order {order_id} cancelled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found or already shipped.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                print(f"Discount applied to Order {order_id}: {discount_percent * 100}%")
            else:
                print(f"Order ID {order_id} not found.")
        else:
            print("Invalid discount percentage. Please enter a value between 0 and 1.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

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

    print("\nOrder List:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    order = manager.get_order(1)
    if order:
        print(f"\nRetrieved Order: Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")
    else:
        print("\nOrder not found.")

    manager.confirm_order(1)
    print(f"\nTotal after confirming Order 1: {manager.get_order_total(1)}")

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    print("\nAfter attempting to cancel Order 1:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    manager.ship_order(2)
    print("\nAfter shipping Order 2:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")