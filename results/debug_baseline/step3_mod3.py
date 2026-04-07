from dataclasses import dataclass
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
        total_items_price = sum(item.price * item.quantity for item in self.items)
        return total_items_price * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            new_order = Order(order_id, items, discount_percent)
            self.orders[order_id] = new_order
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int):
        order = self.get_order(order_id)
        if order:
            if order.status == "PENDING":
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} confirmed.")
            else:
                print(f"Order ID {order_id} is not in PENDING status. Current status: {order.status}")
        else:
            print(f"Order ID {order_id} not found.")

    def ship_order(self, order_id: int):
        order = self.get_order(order_id)
        if order:
            if order.status == "CONFIRMED":
                order.status = "SHIPPED"
                print(f"Order ID {order_id} shipped.")
            else:
                print(f"Order ID {order_id} is not in CONFIRMED status. Current status: {order.status}")
        else:
            print(f"Order ID {order_id} not found.")

    def cancel_order(self, order_id: int):
        order = self.get_order(order_id)
        if order:
            if order.status in ["PENDING", "CONFIRMED"]:
                order.status = "CANCELLED"
                print(f"Order ID {order_id} canceled.")
            elif order.status == "SHIPPED":
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id: int, discount_percent: float):
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
                print(f"Discount applied to Order ID {order_id}. New total: {order.total}")
            else:
                print("Invalid discount percent. Please provide a value between 0.0 and 1.0.")
        else:
            print(f"Order ID {order_id} not found.")

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
    
    item1 = Item(name="item1", price=5.25, quantity=2)
    item2 = Item(name="item2", price=3.75, quantity=1)
    manager.add_order(1, [item1, item2])

    item3 = Item(name="item3", price=5.0, quantity=1)
    manager.add_order(2, [item3])

    print("Order List:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Status: {order.status}, Discount: {order.discount_percent*100}%, Total: {order.total}")

    order = manager.get_order(1)
    if order:
        print(f"\nRetrieved Order ID 1: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Status - {order.status}, Discount - {order.discount_percent*100}%, Total - {order.total}")
    
    manager.confirm_order(1)
    manager.ship_order(1)

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    print("\nAfter Canceling Order ID 1:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Status: {order.status}, Discount: {order.discount_percent*100}%, Total: {order.total}")

    total = manager.get_order_total(2)
    if total:
        print(f"\nOrder ID 2 Total: {total}")

    manager.cancel_order(2)

    print("\nAfter Canceling Order ID 2:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Status: {order.status}, Discount: {order.discount_percent*100}%, Total: {order.total}")

    manager.get_order(1)  # Should return None