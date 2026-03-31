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

    def __init__(self, order_id, items, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.status = status
        self.discount_percent = 0.0
        self.total = self.calculate_total()

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Status: {self.status}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}"


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

    def add_order(self, order_id, items):
        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            print(f"Error: Order with ID {order_id} not found.")
            return

        if order.status == Order.STATUS_SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        elif order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            print(f"Error: Cannot cancel order {order_id} with status {order.status}")

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
            else:
                print("Error: Discount percent must be between 0.0 and 1.0")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CONFIRMED
            order.total = order.calculate_total()
        else:
            print(f"Error: Cannot confirm order {order_id} with status {order.status if order else 'not found'}")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_CONFIRMED:
            order.status = Order.STATUS_SHIPPED
        else:
            print(f"Error: Cannot ship order {order_id} with status {order.status if order else 'not found'}")

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if not order:
            print(f"Error: Order with ID {order_id} not found.")
            return None

        if abs(amount - order.total) > 0.01:  # Allow for small floating-point differences
            raise ValueError(f"Payment amount ({amount}) does not match order total ({order.total})")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1

        order.status = Order.STATUS_CONFIRMED
        order.total = order.calculate_total()  # Recalculate total in case of discounts

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
    order_manager.add_order(1, [Item("Laptop", 1200.00, 1), Item("Mouse", 25.00, 1)])
    order_manager.add_order(2, [Item("Keyboard", 75.00, 1), Item("Monitor", 275.00, 1)])
    order_manager.add_order(3, [Item("Webcam", 50.00, 1), Item("Microphone", 100.00, 1)])

    # Get an order
    order = order_manager.get_order(2)
    if order:
        print(order)

    # List all orders
    print("\nAll Orders:")
    for order in order_manager.list_orders():
        print(order)

    # Apply discount to order 1
    order_manager.apply_discount(1, 0.1)  # 10% discount

    # List orders after discount
    print("\nOrders after discount:")
    for order in order_manager.list_orders():
        print(order)

    # Get total for order 2
    total = order_manager.get_order_total(2)
    if total:
        print(f"\nTotal for Order 2: {total:.2f}")

    # Confirm order 2
    order_manager.confirm_order(2)

    # Process payment for order 1
    try:
        payment = order_manager.process_payment(1, 1225.00, "Credit Card")
        if payment:
            print(f"\nPayment processed: {payment}")
    except ValueError as e:
        print(f"\nError processing payment: {e}")

    # Ship order 2
    order_manager.ship_order(2)

    # Cancel order 1
    try:
        order_manager.cancel_order(1)
    except ValueError as e:
        print(f"\nError cancelling order 1: {e}")

    # List orders after cancellation
    print("\nOrders after cancellation:")
    for order in order_manager.list_orders():
        print(order)

    # Attempt to cancel a shipped order (should raise ValueError)
    order_manager.add_order(4, [Item("Headphones", 100.00, 1)])
    order_manager.confirm_order(4)
    order_manager.ship_order(4)

    try:
        order_manager.cancel_order(4)
    except ValueError as e:
        print(f"\nError cancelling order 4: {e}")

    # Get payment for order 1
    payment = order_manager.get_payment(1)
    if payment:
        print(f"\nPayment for order 1: {payment}")