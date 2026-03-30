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
            raise ValueError("Order ID already exists.")
        if not isinstance(order_id, int):
            raise TypeError("order_id must be an integer.")
        if not isinstance(items, list):
            raise TypeError("items must be a list.")
        if not isinstance(total, float) and not isinstance(total, int):
            raise TypeError("total must be a float or an integer.")
        if total < 0:
            raise ValueError("Total cannot be negative.")

        self.orders[order_id] = Order(order_id, items, total)

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
try:
    order_manager.add_order(1, ["apple", "banana"], 10.0)
    order_manager.add_order(2, ["orange"], 5.0)
except ValueError as e:
    print(f"Error: {e}")
except TypeError as e:
    print(f"Error: {e}")


# 주문 조회
order1 = order_manager.get_order(1)
if order1:
    print(f"Order 1: ID={order1.order_id}, Items={order1.items}, Total={order1.total}")
else:
    print("Order 1 not found.")

# 주문 취소
order_manager.cancel_order(2)

# 모든 주문 목록 조회
all_orders = order_manager.list_orders()
print("All Orders:")
for order in all_orders:
    print(f"  ID={order.order_id}, Items={order.items}, Total={order.total}")

# 예외 처리 테스트
try:
    order_manager.add_order(1, ["apple"], -5.0)
except ValueError as e:
    print(f"Error: {e}")

try:
    order_manager.add_order("a", ["apple"], 5.0)
except TypeError as e:
    print(f"Error: {e}")