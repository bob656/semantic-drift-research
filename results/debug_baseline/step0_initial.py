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


# 사용 예제
order_manager = OrderManager()

# 주문 추가
order_manager.add_order(1, ["item1", "item2"], 100.0)
order_manager.add_order(2, ["item3"], 50.0)

# 주문 조회
order1 = order_manager.get_order(1)
if order1:
    print(order1)
else:
    print("Order not found")

# 주문 목록
all_orders = order_manager.list_orders()
for order in all_orders:
    print(order)

# 주문 취소
order_manager.cancel_order(1)

# 주문 목록 (취소 후)
all_orders = order_manager.list_orders()
for order in all_orders:
    print(order)