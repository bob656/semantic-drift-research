from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id, items, discount_percent=0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = self.calculate_total()

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}"


class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, discount_percent=0.0):
        order = Order(order_id, items, discount_percent)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]

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
    ], discount_percent=0.1)  # Apply 10% discount initially

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
    order_manager.apply_discount(1, 0.2)  # Apply 20% discount

    # List orders after discount application
    print("\nOrders after discount application:")
    for order in order_manager.list_orders():
        print(order)

    # Get total for order 1
    total = order_manager.get_order_total(1)
    if total is not None:
        print(f"\nTotal for Order 1: {total:.2f}")
    else:
        print("\nOrder 1 not found")

    # Cancel an order
    order_manager.cancel_order(2)

    # List orders after cancellation
    print("\nOrders after cancellation:")
    for order in order_manager.list_orders():
        print(order)