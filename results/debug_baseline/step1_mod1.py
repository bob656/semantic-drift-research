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
        total = 0.0
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


# 사용 예제
order_manager = OrderManager()

# 아이템 생성
item1 = Item("item1", 10.0, 2)
item2 = Item("item2", 20.0, 1)
item3 = Item("item3", 5.0, 5)

# 주문 추가
order_manager.add_order(1, [item1, item2])
order_manager.add_order(2, [item3])

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