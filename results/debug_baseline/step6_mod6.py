from dataclasses import dataclass
from typing import List, Optional
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # Added stock field to Item class

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int):
        if item_name in self.items:
            print(f"Item {item_name} already exists. Updating stock.")
        else:
            new_item = Item(name=item_name, price=price, quantity=0, stock=stock)
            self.items[item_name] = new_item
            print(f"Item {item_name} added to inventory.")

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item {item_name} not found.")
            return None

    def reduce_stock(self, item_name: str, quantity: int):
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            item.quantity += quantity  # Update the quantity field in Item class
            print(f"Stock reduced for {item_name}. Remaining stock: {item.stock}")
        else:
            raise ValueError("재고 부족")

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    status: str = "PENDING"
    created_at: datetime.datetime = datetime.datetime.now()  # Added created_at field to Order class

    def calculate_total(self) -> float:
        total_items_price = sum(item.price * item.quantity for item in self.items)
        return total_items_price * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            try:
                for item in items:
                    inventory.reduce_stock(item.name, item.quantity)
                new_order = Order(order_id, items, discount_percent=0.0)
                self.orders[order_id] = new_order
                print(f"Order ID {order_id} added with reduced stock.")
            except ValueError as e:
                for item in items:
                    inventory.add_item(item.name, item.price, item.quantity)  # Revert changes if any stock reduction fails
                raise ValueError(e)

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
                for item in order.items:
                    inventory.add_item(item.name, item.price, item.quantity)  # Revert changes by adding stock back
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
        return sorted(list(self.orders.values()), key=lambda x: x.created_at)

    def get_order_history(self) -> List[Order]:
        return sorted(list(self.orders.values()), key=lambda x: x.created_at, reverse=True)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [order for order in self.orders.values() if order.status == status]

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if order:
            if amount == order.total and order.status == "PENDING":
                payment_id = len(self.payments) + 1
                new_payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = new_payment
                order.status = "CONFIRMED"
                print(f"Payment processed for Order ID {order_id}. New status: CONFIRMED.")
                return new_payment
            else:
                if amount != order.total:
                    raise ValueError("Payment amount does not match the order total.")
                elif order.status != "PENDING":
                    raise ValueError("Order must be in PENDING status to process payment.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 5.25, 10)
    inventory.add_item("item2", 3.75, 5)
    inventory.add_item("item3", 5.0, 8)

    manager = OrderManager()

    item1 = Item(name="item1", price=5.25, quantity=2, stock=0)
    item2 = Item(name="item2", price=3.75, quantity=1, stock=0)
    item3 = Item(name="item3", price=5.0, quantity=4, stock=0)

    try:
        manager.add_order(1, [item1, item2], inventory)
    except ValueError as e:
        print(e)

    try:
        manager.add_order(2, [item3], inventory)
    except ValueError as e:
        print(e)

    order = manager.get_order(1)
    if order:
        print(f"Order ID 1 Details: Total - {order.total}, Status - {order.status}")

    stock = inventory.get_stock("item1")
    if stock is not None:
        print(f"Stock for item1: {stock}")

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    order = manager.get_order(1)
    if order:
        print(f"Order ID 1 Details after cancellation: Total - {order.total}, Status - {order.status}")

    stock = inventory.get_stock("item1")
    if stock is not None:
        print(f"Stock for item1 after cancellation: {stock}")

    # 주문 이력 확인
    order_history = manager.get_order_history()
    for order in order_history:
        print(f"Order ID - {order.order_id}, Status - {order.status}, Created At - {order.created_at}")

    # 상태별 주문 확인
    cancelled_orders = manager.get_orders_by_status("CANCELLED")
    for order in cancelled_orders:
        print(f"Cancelled Order ID - {order.order_id}")