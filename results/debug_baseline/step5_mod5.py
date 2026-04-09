from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int = 0

class Inventory:
    def __init__(self):
        self.items: Dict[str, Item] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            print(f"Item {item_name} already exists.")
            return
        self.items[item_name] = Item(item_name, price, 0, stock)
        print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item {item_name} not found.")
            return None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Stock reduced for {item_name}. Remaining stock: {item.stock}")
        else:
            raise ValueError("재고 부족")

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
        self.orders: Dict[int, Order] = {}
        self.payments: Dict[int, Payment] = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return

        for item in items:
            stock = inventory.get_stock(item.name)
            if stock is None or stock < item.quantity:
                raise ValueError(f"재고 부족: {item.name}")

        try:
            for item in items:
                inventory.reduce_stock(item.name, item.quantity)

            self.orders[order_id] = Order(order_id, items)
            print(f"Order {order_id} added.")
        except ValueError as e:
            print(e)

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

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if not order:
            print(f"Order ID {order_id} not found.")
            return None

        if amount != order.total:
            raise ValueError("Amount does not match the order total.")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "CONFIRMED"
        print(f"Payment processed for Order {order_id} using {method}.")
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 25.0, 10)
    inventory.add_item("item2", 10.0, 15)
    inventory.add_item("item3", 20.0, 8)

    manager = OrderManager()

    item1 = Item("item1", 25.0, 2)
    item2 = Item("item2", 10.0, 3)
    item3 = Item("item3", 20.0, 1)

    try:
        manager.add_order(1, [item1, item2], inventory)
        manager.add_order(2, [item3], inventory)
    except ValueError as e:
        print(e)

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

    try:
        manager.add_order(3, [Item("item1", 25.0, 8)], inventory)
    except ValueError as e:
        print(e)

    manager.ship_order(2)
    print(f"\nOrder 2 Status after shipping: {manager.get_order(2).status}")

    try:
        payment = manager.process_payment(1, 70.0, "Credit Card")
        if payment:
            print(f"\nPayment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    except ValueError as e:
        print(e)

    order = manager.get_order(1)
    if order:
        print(f"\nOrder 1 Status after payment: {order.status}")
    else:
        print("\nOrder not found.")

    payment_info = manager.get_payment(1)
    if payment_info:
        print(f"\nPayment Info for Order 1: Payment ID: {payment_info.payment_id}, Amount: {payment_info.amount}, Method: {payment_info.method}")
    else:
        print("\nNo payment info found.")