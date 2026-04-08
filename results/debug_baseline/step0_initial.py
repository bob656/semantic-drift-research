class Order:
    def __init__(self, order_id, items, total):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, total):
        if order_id not in self.orders:
            self.orders[order_id] = Order(order_id, items, total)
            return True
        return False

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def list_orders(self):
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    manager.add_order(1, ["item1", "item2"], 50.0)
    manager.add_order(2, ["item3"], 30.0)

    print("주문 목록:")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")

    print("\n주문 조회 (ID: 1):")
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")
    else:
        print("주문을 찾을 수 없습니다.")

    print("\n주문 취소 (ID: 2):")
    if manager.cancel_order(2):
        print("주문이 취소되었습니다.")
    else:
        print("취소할 주문을 찾을 수 없습니다.")

    print("\n주문 목록 (취소 후):")
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")