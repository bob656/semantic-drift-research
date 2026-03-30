from dataclasses import dataclass

@dataclass
class Customer:
    customer_id: int
    name: str
    email: str

class Item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.refunded = False

class Order:
    def __init__(self, order_id, items, inventory, customer_id):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)
        self.status = "PENDING"
        self.payment = None
        self.discount_percent = 0.0
        self.customer_id = customer_id
        self.created_at = None

    def _calculate_total(self):
        return self.total * (1 - self.discount_percent)


class OrderManager:
    def __init__(self, inventory):
        self.orders = {}
        self.payments = {}
        self.customers = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_customer(self, customer_id, name, email):
        if customer_id in self.customers:
            raise ValueError(f"Customer ID {customer_id} already exists.")
        self.customers[customer_id] = Customer(customer_id, name, email)

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def add_order(self, order_id, items, inventory, customer_id):
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists.")

        if customer_id not in self.customers:
            raise ValueError(f"Customer ID {customer_id} does not exist.")

        for item_name in [item.name for item in items]:
            if self.inventory.get_stock(item_name) < next(item.quantity for item in items if item.name == item_name):
                raise ValueError(f"재고 부족: {item_name}")

        order = Order(order_id, items, inventory, customer_id)
        self.orders[order_id] = order

        for item in items:
            self.inventory.reduce_stock(item.name, item.quantity)

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        order.status = "CANCELLED"

        for item in order.items:
            self.inventory.add_item(item.name, item.price, item.quantity)

    def confirm_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "PENDING":
            raise ValueError("주문 상태가 PENDING가 아니면 확인할 수 없습니다.")
        order.status = "CONFIRMED"
        order.total = order._calculate_total()

    def ship_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "CONFIRMED":
            raise ValueError("주문 상태가 CONFIRMED가 아니면 배송할 수 없습니다.")
        order.status = "SHIPPED"

    def list_orders(self):
        return [(order.order_id, order.status, order.total) for order in self.orders.values() if order.status != "CANCELLED"]

    def apply_discount(self, order_id, discount_percent):
        if order_id not in self.orders:
            raise KeyError(f"Order ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = self.orders[order_id]._calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise KeyError(f"Order ID {order_id} not found.")

        if order.payment:
            raise ValueError(f"Order {order_id} has already been paid.")

        if abs(amount - order.total) > 0.001:  # Allow for small floating-point differences
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[self.next_payment_id] = payment
        order.payment = payment
        order.status = "CONFIRMED"
        order.total = order._calculate_total()
        self.next_payment_id += 1
        return payment

    def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    def get_order_history(self):
        return list(self.orders.values())

    def get_orders_by_status(self, status):
        return [order for order in self.orders.values() if order.status == status]

    def refund_payment(self, order_id):
        order = self.get_order(order_id)
        if not order:
            raise KeyError(f"Order ID {order_id} not found.")
        if not order.payment:
            raise ValueError(f"Order {order_id} has not been paid.")
        if order.payment.refunded:
            raise ValueError(f"Order {order_id} has already been refunded.")

        order.payment.refunded = True
        order.status = "REFUNDED"

    def get_refunded_orders(self):
        return [order for order in self.orders.values() if order.status == "REFUNDED"]

    def get_orders_by_customer(self, customer_id):
        return [order for order in self.orders.values() if order.customer_id == customer_id]


# Inventory class (needed for the OrderManager)
class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, name, price, quantity):
        self.items[name] = {"price": price, "quantity": quantity}

    def get_stock(self, name):
        return self.items.get(name, {}).get("quantity", 0)

    def reduce_stock(self, name, quantity):
        if name in self.items:
            self.items[name]["quantity"] -= quantity
        else:
            raise ValueError(f"Item {name} not found in inventory.")


# 사용 예제
inventory = Inventory()
inventory.add_item("item1", 10.0, 5)
inventory.add_item("item2", 5.0, 3)
inventory.add_item("item3", 20.0, 2)

order_manager = OrderManager(inventory)

# Add a customer
order_manager.add_customer(1, "Alice", "alice@example.com")

try:
    order_manager.add_order(1, [Item("item1", 10.0, 2), Item("item2", 5.0, 3)], inventory, 1)
    order_manager.add_order(2, [Item("item3", 20.0, 1)], inventory, 1)

    order