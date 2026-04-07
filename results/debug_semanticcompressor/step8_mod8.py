from typing import List, Optional
from dataclasses import dataclass
import datetime

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 추가된 재고 필드

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str
    refunded: bool = False  # 환불 여부 필드 추가

@dataclass
class Customer:
    customer_id: int
    name: str
    email: str

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            raise ValueError(f"Item '{item_name}' already exists.")
        self.items[item_name] = {'price': price, 'stock': stock}

    def get_stock(self, item_name: str) -> Optional[int]:
        return self.items.get(item_name, {}).get('stock')

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items:
            raise ValueError(f"Item '{item_name}' does not exist.")
        
        current_stock = self.items[item_name]['stock']
        if quantity > current_stock:
            raise ValueError(f"재고 부족: {item_name}")
        
        self.items[item_name]['stock'] -= quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], customer_id: int, discount_percent: float = 0.0):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = "PENDING"  # 추가된 상태 필드
        self.created_at = datetime.datetime.now()  # 주문 생성 시각

    def apply_discount(self, discount_percent: float) -> None:
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}
        self.customers = {}

    def add_customer(self, customer_id: int, name: str, email: str) -> None:
        if customer_id in self.customers:
            raise ValueError(f"Customer with ID {customer_id} already exists.")
        self.customers[customer_id] = Customer(customer_id, name, email)

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory, customer_id: int) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order with ID {order_id} already exists.")
        
        if customer_id not in self.customers:
            raise ValueError(f"Customer with ID {customer_id} does not exist.")

        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        self.orders[order_id] = Order(order_id, items, customer_id)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError("주문 상태가 PENDING이 아닙니다")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError("주문 상태가 CONFIRMED이 아닙니다")

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        order.apply_discount(discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
        if order.status != "CONFIRMED":
            raise ValueError("주문 상태가 CONFIRMED이 아닙니다")
        
        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        
        return payment

    def get_payment(self, order_id: int) -> Optional[Payment]:
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def refund_payment(self, order_id: int) -> None:
        payment = self.get_payment(order_id)
        if payment is None:
            raise ValueError(f"No payment found for Order ID {order_id}")
        
        if payment.refunded:
            raise ValueError("Payment already refunded")
        
        payment.refunded = True
        order = self.get_order(order_id)
        if order:
            order.status = "REFUNDED"

    def get_refunded_orders(self) -> List[Order]:
        return [order for order in self.orders.values() if order.status == "REFUNDED"]

    def get_order_history(self) -> List[Order]:
        return sorted(self.orders.values(), key=lambda order: order.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        valid_statuses = ["PENDING", "CONFIRMED", "SHIPPED", "CANCELLED", "REFUNDED"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Choose from {valid_statuses}")
        
        return [order for order in self.orders.values() if order.status == status]

    def get_orders_by_customer(self, customer_id: int) -> List[Order]:
        if customer_id not in self.customers:
            raise ValueError(f"Customer with ID {customer_id} does not exist.")
        return [order for order in self.orders.values() if order.customer_id == customer_id]

# Example usage
if __name__ == "__main__":
    manager = OrderManager()

    # Add customers
    manager.add_customer(1, "Alice", "alice@example.com")
    manager.add_customer(2, "Bob", "bob@example.com")

    # Add items to inventory
    manager.inventory.add_item("Laptop", 1000, 5)
    manager.inventory.add_item("Mouse", 25, 20)

    # Create orders for customers
    order1 = Order(order_id=1, items=[Item(name="Laptop", price=1000, quantity=1)], customer_id=1)
    order2 = Order(order_id=2, items=[Item(name="Mouse", price=25, quantity=2)], customer_id=2)

    # Add orders to manager
    manager.add_order(order1.order_id, order1.items, manager.inventory, order1.customer_id)
    manager.add_order(order2.order_id, order2.items, manager.inventory, order2.customer_id)

    # Get orders by customer
    alice_orders = manager.get_orders_by_customer(1)
    bob_orders = manager.get_orders_by_customer(2)

    print("Alice's Orders:")
    for order in alice_orders:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}, Status: {order.status}")

    print("\nBob's Orders:")
    for order in bob_orders:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}, Status: {order.status}")