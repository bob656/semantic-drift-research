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
class Customer:
    customer_id: int
    name: str
    email: str

@dataclass
class Order:
    order_id: int
    items: List[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"  # 기본 상태는 PENDING
    customer_id: int = 0  # 고객 ID 추가
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
        self.customers = {}

    def add_customer(self, customer_id: int, name: str, email: str) -> None:
        if customer_id in self.customers:
            print(f"Customer ID {customer_id} already exists.")
        else:
            self.customers[customer_id] = Customer(customer_id, name, email)
            print(f"Customer with ID {customer_id} added.")

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory, customer_id: int) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
            return

        if customer_id not in self.customers:
            raise ValueError(f"Customer ID {customer_id} does not exist.")

        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                print(e)
                return

        total = sum(item.price * item.quantity for item in items)
        self.orders[order_id] = Order(order_id=order_id, items=items, total=total, customer_id=customer_id)
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

    def get_orders_by_customer(self, customer_id: int) -> List[Order]:
        return [order for order in self.orders.values() if order.customer_id == customer_id]

# 사용 예시
inventory = Inventory()
inventory.add_item("Item1", 10.0, 5)
customer_manager = OrderManager()
customer_manager.add_customer(1, "John Doe", "john.doe@example.com")
order_manager = OrderManager()

try:
    order_manager.add_order(1, [Item(name="Item1", price=10.0, quantity=1)], inventory, 1)
except ValueError as e:
    print(e)

# 주문 이력 조회
for order in order_manager.get_order_history():
    print(f"Order {order.order_id} (Created At: {order.created_at}, Customer ID: {order.customer_id}, Status: {order.status}): Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")

# 특정 고객의 주문 조회
for order in order_manager.get_orders_by_customer(1):
    print(f"Order {order.order_id} (Customer ID: {order.customer_id}, Status: {order.status}): Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")