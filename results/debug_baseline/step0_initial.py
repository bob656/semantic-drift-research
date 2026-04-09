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
            return
        self.orders[order_id] = Order(order_id, items, total)
        print(f"Order {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order {order_id} cancelled.")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    manager.add_order(1, ["item1", "item2"], 50.0)
    manager.add_order(2, ["item3"], 20.0)

    print("Order List:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    order = manager.get_order(1)
    if order:
        print(f"\nRetrieved Order: Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")
    else:
        print("\nOrder not found.")

    manager.cancel_order(1)
    print("\nAfter cancelling Order 1:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")