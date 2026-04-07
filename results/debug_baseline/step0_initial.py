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
            self.orders[order_id] = Order(order_id, items, total)
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
    
    # 주문 추가
    manager.add_order(1, ["item1", "item2"], 50.0)
    manager.add_order(2, ["item3"], 20.0)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {order.items}, Total - {order.total}")

    # 모든 주문 목록
    all_orders = manager.list_orders()
    for order in all_orders:
        print(f"Order {order.order_id}: Items - {order.items}, Total - {order.total}")

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후 다시 조회
    canceled_order = manager.get_order(1)
    if not canceled_order:
        print("Order 1 has been canceled.")