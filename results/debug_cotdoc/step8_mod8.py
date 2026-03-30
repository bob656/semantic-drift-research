class Item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

class Customer:
    def __init__(self, customer_id, name, email):
        self.customer_id = customer_id
        self.name = name
        self.email = email

class Order:
    def __init__(self, order_id, items, customer_id):
        self.order_id = order_id
        self.items = items
        self.customer_id = customer_id
        self.discount_percent = 0.0
        self.total = self.calculate_total()
        self.status = "PENDING"
        self.created_at = datetime.datetime.now()

    def calculate_total(self):
        """
        주문 항목의 총 가격을 계산합니다.
        """
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)

class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.refunded = False  # Add refunded attribute

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = {'price': price, 'stock': stock}

    def get_stock(self, item_name):
        return self.items.get(item_name, {}).get('stock', 0)

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items or self.items[item_name]['stock'] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name]['stock'] -= quantity

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}
        self.customers = {}
        self.next_payment_id = 1

    def add_customer(self, customer_id, name, email):
        if customer_id in self.customers:
            raise ValueError(f"Customer ID {customer_id} already exists")
        self.customers[customer_id] = Customer(customer_id, name, email)

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def add_order(self, order_id, items, customer_id):
        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists")
        if customer_id not in self.customers:
            raise ValueError(f"Customer ID {customer_id} does not exist")

        # for item in items:  # Removed inventory reduction here
        #     inventory.reduce_stock(item.name, item.quantity)

        order = Order(order_id, items, customer_id)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            return

        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        order.status = "CANCELLED"

    def list_orders(self):
        return [(order_id, order) for order_id, order in self.orders.items()]

    def apply_discount(self, order_id, discount_percent):
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")

        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order ID {order_id} does not exist")

        if abs(amount - order.total) > 0.001:
            raise ValueError(f"Payment amount {amount} does not match order total {order.total}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = "CONFIRMED"
        return payment

    def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    def refund_payment(self, payment_id):
        payment = self.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment ID {payment_id} does not exist")

        if payment.refunded:
            raise ValueError(f"Payment {payment_id} has already been refunded")

        payment.refunded = True
        order_id = payment.order_id
        order = self.get_order(order_id)
        if order:
            order.status = "REFUNDED"  # Add REFUNDED status

    def get_refunded_orders(self):
        refunded_orders = []
        for order_id, order in self.orders.items():
            if order.status == "REFUNDED":
                refunded_orders.append((order_id, order))
        return refunded_orders

    def get_order_history(self):
        return sorted([(order_id, order) for order_id, order in self.orders.items()],
                      key=lambda item: item[1].created_at, reverse=True)

    def get_orders_by_customer(self, customer_id):
        return [(order_id, order) for order_id, order in self.orders.items() if order.customer_id == customer_id]


import datetime

# Example Usage (Illustrative -  replace with your actual setup)
order_manager = OrderManager()
item1 = Item("Product A", 10.0, 5)
item2 = Item("Product B", 20.0, 2)

# Add a customer
order_manager.add_customer(1, "John Doe", "john.doe@example.com")

# Add an order for the customer
order_manager.add_order(1, [item1, item2], 1)

payment = order_manager.process_payment(1, 30.0, "Credit Card")

order_manager.refund_payment(payment.payment_id)

refunded_orders = order_manager.get_refunded_orders()
print(f"Refunded Orders: {refunded_orders}")

# Get orders by customer
customer_orders = order_manager.get_orders_by_customer(1)
print(f"Orders by Customer 1: {customer_orders}")