from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            raise ValueError(f"Item '{item_name}' already exists in inventory")
        self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        return item.stock if item else None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if not item or item.stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        item.stock -= quantity
        item.quantity += quantity

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = Order.STATUS_PENDING
        self.total = self.calculate_total()
        self.created_at = datetime.now()

    def calculate_total(self) -> float:
        total = sum(item.price * item.quantity for item in self.items)
        return total - (total * self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status == Order.STATUS_SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            raise ValueError("이미 취소된 주문입니다")

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CONFIRMED
        else:
            raise ValueError(f"주문 상태가 {order.status}이므로 확인할 수 없습니다")

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if order.status == Order.STATUS_CONFIRMED:
            order.status = Order.STATUS_SHIPPED
        else:
            raise ValueError(f"주문 상태가 {order.status}이므로 배송할 수 없습니다")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = self.orders[order_id].calculate_total()

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        if order_id not in self.orders:
            raise ValueError("Order ID does not exist")
        order = self.orders[order_id]
        if amount != order.total:
            raise ValueError(f"Amount {amount} does not match the total {order.total}")
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = Order.STATUS_CONFIRMED
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def list_orders(self) -> List[Order]:
        return sorted([order for order in self.orders.values() if order.status != Order.STATUS_CANCELLED], key=lambda x: x.created_at)

    def get_order_history(self) -> List[Order]:
        return sorted(list(self.orders.values()), key=lambda x: x.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    inventory = Inventory()
    inventory.add_item("item1", 20.99, 5)
    inventory.add_item("item2", 5.99, 10)
    inventory.add_item("item3", 20.00, 3)

    manager = OrderManager()
    try:
        manager.add_order(1, [inventory.items["item1"], inventory.items["item2"]], inventory)
        manager.add_order(2, [inventory.items["item3"]], inventory)
    except ValueError as e:
        print(e)

    order = manager.get_order(1)
    if order:
        print("Order 1:", [f"{item.name} x {item.quantity}" for item in order.items])  # 출력: ['item1 x 2', 'item2 x 3']
        print(f"Total: ${order.total}")

    print("All orders:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: ${order.total}")

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    print("After canceling Order 1, all orders:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: ${order.total}")

    try:
        payment = manager.process_payment(2, 20.00, "credit")
        print(f"Payment processed: ID={payment.payment_id}, Method={payment.method}")
        manager.confirm_order(2)
        manager.ship_order(2)
    except ValueError as e:
        print(e)

    print("After processing payment and confirming/shipping Order 2, all orders:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, Total: ${order.total}")

    print("Order history (including cancelled):")
    for order in manager.get_order_history():
        print(f"ID: {order.order_id}, Status: {order.status}, Created At: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print("Orders by status 'CANCELLED':")
    for order in manager.get_orders_by_status(Order.STATUS_CANCELLED):
        print(f"ID: {order.order_id}, Status: {order.status}, Created At: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")