from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total:.2f}, Discount: {self.discount_percent:.2f}, Status: {self.status}"

    def calculate_total(self):
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 - self.discount_percent)


class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method


class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}
        self.next_payment_id = 1

    def add_order(self, order_id, items, discount_percent=0.0):
        order = Order(order_id, items, discount_percent)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            print(f"Order with ID {order_id} not found.")
            return

        if order.status == Order.STATUS_SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            print(f"Order with ID {order_id} is already cancelled.")

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
            else:
                print(f"Order with ID {order_id} not found.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_PENDING:
                order.status = Order.STATUS_CONFIRMED
            else:
                print(f"Order with ID {order_id} is not in PENDING status.")
        else:
            print(f"Order with ID {order_id} not found.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_CONFIRMED:
                order.status = Order.STATUS_SHIPPED
            else:
                print(f"Order with ID {order_id} is not in CONFIRMED status.")
        else:
            print(f"Order with ID {order_id} not found.")

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            print(f"Order with ID {order_id} not found.")
            return None

        if abs(order.total - amount) > 0.01:  # Allow for small floating-point differences
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total:.2f}, 결제 금액: {amount:.2f}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = Order.STATUS_CONFIRMED
        return payment

    def get_payment(self, order_id):
        for payment_id, payment in self.payments.items():
            if payment.order_id == order_id:
                return payment
        return None


# Example Usage
if __name__ == "__main__":
    order_manager = OrderManager()

    # Add orders
    order_manager.add_order(1, [
        Item("Laptop", 1200.00, 1),
        Item("Mouse", 25.00, 1)
    ])
    order_manager.add_order(2, [
        Item("Keyboard", 75.00, 1),
        Item("Monitor", 275.00, 1)
    ])
    order_manager.add_order(3, [
        Item("Webcam", 50.00, 1),
        Item("Microphone", 100.00, 1)
    ], discount_percent=0.1)  # Apply 10% discount initially

    # List all orders
    print("All Orders:")
    for order in order_manager.list_orders():
        print(order)

    # Get a specific order
    order = order_manager.get_order(2)
    print("\nOrder with ID 2:")
    print(order)

    # Apply discount to order 1
    order_manager.apply_discount(1, 0.2)  # Apply 20% discount

    # Get the total for order 1
    total = order_manager.get_order_total(1)
    print(f"\nTotal for order 1 after discount: {total:.2f}")

    # List all orders again to see updated totals
    print("\nAll Orders after applying discounts:")
    for order in order_manager.list_orders():
        print(order)

    # Confirm order 2
    order_manager.confirm_order(2)

    # Ship order 2
    order_manager.ship_order(2)

    # Try to cancel order 1
    try:
        order_manager.cancel_order(1)
    except ValueError as e:
        print(f"\nError: {e}")

    # List all orders again to see updated status
    print("\nAll Orders after cancellation:")
    for order in order_manager.list_orders():
        print(order)

    # Try to cancel order 2 (already shipped)
    try:
        order_manager.cancel_order(2)
    except ValueError as e:
        print(f"\nError: {e}")

    # Process payment for order 1
    try:
        payment = order_manager.process_payment(1, order_manager.get_order(1).total, "Credit Card")
        print(f"\nPayment processed: {payment}")
    except ValueError as e:
        print(f"\nError: {e}")

    # Get payment for order 1
    payment = order_manager.get_payment(1)
    if payment:
        print(f"\nPayment details for order 1: {payment}")

    # Try to process payment with incorrect amount
    try:
        order_manager.process_payment(1, order_manager.get_order(1).total + 1, "Credit Card")
    except ValueError as e:
        print(f"\nError: {e}")