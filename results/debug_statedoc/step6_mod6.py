from datetime import datetime

class Order:
    def __init__(self, order_id, items, discount_percent=0.0, status="PENDING"):
        self.order_id = order_id
        self.items = items
        self.created_at = datetime.now()
        self.discount_percent = discount_percent
        self.total = self.calculate_total()
        self.status = status

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)

    def __repr__(self):
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, status={self.status})"


class Item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Item(name={self.name}, price={self.price}, quantity={self.quantity})"


class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = (price, stock)

    def get_stock(self, item_name):
        if item_name not in self.items:
            return 0
        return self.items[item_name][1]

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items:
            raise ValueError(f"Item {item_name} not found in inventory.")
        price, stock = self.items[item_name]
        if stock < quantity:
            raise ValueError(f"Not enough stock for {item_name}. Available: {stock}, Requested: {quantity}")
        self.items[item_name] = (price, stock - quantity)


class OrderManager:
    def __init__(self, inventory):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id, items):
        if order_id in self.orders:
            raise ValueError("Duplicate order ID.")

        for item_name, quantity in items:
            self.inventory.reduce_stock(item_name, quantity)

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        order.status = "CANCELLED"

        # Restore stock
        for item_name, quantity in order.items:
            self.inventory.add_item(item_name, self.inventory.get_stock(item_name), quantity)

    def list_orders(self):
        return [order for order in self.orders.values() if order.status not in ("CANCELLED")]

    def apply_discount(self, order_id, discount_percent):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0.")
        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        return self.orders[order_id].total

    def confirm_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "PENDING":
            raise ValueError(f"주문 상태가 PENDING가 아닙니다. 현재 상태: {order.status}")
        order.status = "CONFIRMED"

    def ship_order(self, order_id):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]
        if order.status != "CONFIRMED":
            raise ValueError(f"주문 상태가 CONFIRMED가 아닙니다. 현재 상태: {order.status}")
        order.status = "SHIPPED"

    def process_payment(self, order_id, amount, method):
        if order_id not in self.orders:
            raise KeyError(f"Order with ID {order_id} not found.")
        order = self.orders[order_id]

        if abs(amount - order.total) > 0.01:  # Allow for slight floating-point inaccuracies
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = "CONFIRMED"  # Update order status after successful payment
        return payment

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None

    def get_order_history(self):
        return list(self.orders.values())

    def get_orders_by_status(self, status):
        return [order for order in self.orders.values() if order.status == status]


class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method

    def __repr__(self):
        return f"Payment(payment_id={self.payment_id}, order_id={self.order_id}, amount={self.amount}, method={self.method})"


# 사용 예제
inventory = Inventory()
inventory.add_item("item1", 10.0, 10)
inventory.add_item("item2", 20.0, 5)
inventory.add_item("item3", 5.0, 10)

order_manager = OrderManager(inventory)

# Create some orders
order_manager.add_order(1, [("item1", 2), ("item2", 1)])
order_manager.add_order(2, [("item3", 3)])
order_manager.add_order(3, [("item1", 1)])


# Get order history
order_history = order_manager.get_order_history()
print("Order History:")
for order in order_history:
    print(order)

# Get orders by status
pending_orders = order_manager.get_orders_by_status("PENDING")
print("\nPending Orders:")
for order in pending_orders:
    print(order)

# Cancel order 3
order_manager.cancel_order(3)
print("\nAfter canceling order 3:")

# Get order history again
order_history = order_manager.get_order_history()
print("Order History:")
for order in order_history:
    print(order)

# Confirm and ship order 1
order_manager.confirm_order(1)
order_manager.ship_order(1)

# Get order history again
order_history = order_manager.get_order_history()
print("\nOrder History after confirming and shipping order 1:")
for order in order_history:
    print(order)