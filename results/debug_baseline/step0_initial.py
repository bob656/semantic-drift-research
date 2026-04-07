class Order:
    def __init__(self, order_id, items, total):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, total):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            new_order = Order(order_id, items, total)
            self.orders[order_id] = new_order
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order ID {order_id} canceled.")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    manager.add_order(1, ["item1", "item2"], 10.5)
    manager.add_order(2, ["item3"], 5.0)

    print("Order List:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    order = manager.get_order(1)
    if order:
        print(f"\nRetrieved Order ID 1: Items - {order.items}, Total - {order.total}")
    
    manager.cancel_order(1)
    print("\nAfter Canceling Order ID 1:")
    for order in manager.list_orders():
        print(f"ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    manager.get_order(1)  # Should return None