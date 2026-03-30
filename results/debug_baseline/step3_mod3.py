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

    def calculate_total(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        return subtotal * (1 - self.discount_percent)

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Status: {self.status}"


class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, discount_percent=0.0):
        order = Order(order_id, items, discount_percent)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            return  # Order not found, nothing to cancel

        if order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            order.status = Order.STATUS_CANCELLED
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CONFIRMED
            order.total = order.calculate_total()

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == Order.STATUS_CONFIRMED:
            order.status = Order.STATUS_SHIPPED

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
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
    ])

    # Get an order
    order = order_manager.get_order(2)
    if order:
        print(order)
    else:
        print("Order not found")

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
    else:
        print("Order not found")

    # Confirm order 2
    order_manager.confirm_order(2)
    print("\nOrder 2 after confirmation:")
    print(order_manager.get_order(2))

    # Ship order 2
    order_manager.ship_order(2)
    print("\nOrder 2 after shipping:")
    print(order_manager.get_order(2))

    # Cancel order 1
    try:
        order_manager.cancel_order(1)
        print("\nOrder 1 after cancellation:")
        print(order_manager.get_order(1))
    except ValueError as e:
        print(e)

    # Attempt to cancel a shipped order (should raise ValueError)
    try:
        order_manager.cancel_order(2)
    except ValueError as e:
        print(f"\nCaught expected error: {e}")

    # List orders after cancellation
    print("\nOrders after cancellation:")
    for order in order_manager.list_orders():
        print(order)