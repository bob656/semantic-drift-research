from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = items
        self.total = self.calculate_total()

    def calculate_total(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total}"


class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items):
        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]

    def list_orders(self):
        return list(self.orders.values())


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

    # Cancel an order
    order_manager.cancel_order(1)

    # List orders after cancellation
    print("\nOrders after cancellation:")
    for order in order_manager.list_orders():
        print(order)