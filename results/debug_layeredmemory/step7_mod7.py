from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 현재 재고 수량

class Payment:
    def __init__(self, payment_id: int, order_id: int, amount: float, method: str, refunded: bool = False):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.refunded = refunded

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"  # 기본 상태는 PENDING
    created_at: datetime = datetime.now()  # 주문 생성 시각

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            print(f"Item '{item_name}' already exists. Updating stock.")
        self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
        print(f"Item '{item_name}' added to inventory with stock {stock}.")

    def get_stock(self, item_name: str) -> Optional[int]:
        if item_name in self.items:
            return self.items[item_name].stock
        else:
            print(f"No item found with name '{item_name}'.")
            return None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name in self.items and self.items[item_name].stock >= quantity:
            self.items[item_name].stock -= quantity
            print(f"Reduced stock for '{item_name}' by {quantity}. Remaining stock: {self.items[item_name].stock}")
        else:
            raise ValueError("재고 부족")

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return

        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                print(e)
                return

        total = sum(item.price * item.quantity for item in items)
        self.orders[order_id] = Order(order_id=order_id, items=items, total=total)
        print(f"Order with ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order:
            if order.status in ["PENDING", "CONFIRMED"]:
                order.status = "CANCELLED"
                print(f"Order with ID {order_id} canceled.")
            elif order.status == "SHIPPED":
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"No order found with ID {order_id}.")

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order with ID {order_id} confirmed.")
        else:
            print(f"No pending order found with ID {order_id}.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order with ID {order_id} shipped.")
        else:
            print(f"No confirmed order found with ID {order_id}.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total *= (1 - discount_percent)
                print(f"Discount applied to Order ID {order_id}. New total: {order.total}")
            else:
                print(f"No order found with ID {order_id}.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}.")
            return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if amount != order.total:
                raise ValueError("Payment amount does not match the total.")
            payment_id = len(self.payments) + 1
            payment = Payment(payment_id, order_id, amount, method)
            self.payments[payment_id] = payment
            order.status = "CONFIRMED"
            print(f"Order with ID {order_id} confirmed via payment.")
            return payment
        else:
            raise ValueError("Invalid order status for payment.")

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"No payment found for Order ID {order_id}.")
        return None

    def refund_payment(self, order_id: int) -> None:
        payment = self.get_payment(order_id)
        if payment and not payment.refunded:
            payment.refunded = True
            order = self.get_order(order_id)
            if order:
                order.status = "REFUNDED"
                print(f"Payment for Order ID {order_id} refunded.")
            else:
                print(f"No order found with ID {order_id}.")
        elif payment and payment.refunded:
            raise ValueError("Payment already refunded.")

    def get_refunded_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status == "REFUNDED"]

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda x: x.created_at)

# 사용 예시
inventory = Inventory()
inventory.add_item("Item1", 10, 100)
order_manager = OrderManager()

# 주문 추가
items = [Item(name="Item1", price=10, quantity=5)]
order_manager.add_order(1, items, inventory)

# 결제 처리
try:
    payment = order_manager.process_payment(1, 50, "Credit Card")
except ValueError as e:
    print(e)

# 환불 처리
try:
    order_manager.refund_payment(1)
except ValueError as e:
    print(e)

# 환불된 주문 조회
for order in order_manager.get_refunded_orders():
    print(f"Order {order.order_id} (Status: {order.status}): Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")

# 주문 이력 조회
for order in order_manager.get_order_history():
    print(f"Order {order.order_id} (Created At: {order.created_at}, Status: {order.status}): Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")