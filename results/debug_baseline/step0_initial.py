class Order:
    def __init__(self, order_id, items, total):
        self.order_id = order_id
        self.items = items
        self.total = total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Total: {self.total}"


class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, total):
        order = Order(order_id, items, total)
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
    order_manager.add_order(1, ["Laptop", "Mouse"], 1200.00)
    order_manager.add_order(2, ["Keyboard", "Monitor"], 350.00)
    order_manager.add_order(3, ["Webcam", "Microphone"], 150.00)

    # Get an order
    order = order_manager.get_order(2)
    if order:
        print(order)

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