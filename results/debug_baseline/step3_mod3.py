from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int


class Order:
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(self, order_id, items, discount_percent=0.0, status=STATUS_PENDING):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = status
        self.total = self.calculate_total()

    def calculate_total(self):
        total = 0.0
        for item in self.items:
            total += item.price * item.quantity
        total -= total * self.discount_percent
        return total

    def __str__(self):
        return f"Order ID: {self.order_id}, Items: {self.items}, Discount: {self.discount_percent:.2f}, Total: {self.total:.2f}, Status: {self.status}"


class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, discount_percent=0.0):
        order = Order(order_id, items, discount_percent)
        self.orders[order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if not order:
            print(f"Order with ID {order_id} not found.")
            return

        if order.status not in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            raise ValueError(f"Cannot cancel order {order_id}. Status is {order.status}")

        order.status = Order.STATUS_CANCELLED

    def list_orders(self):
        return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
            else:
                print(f"Order with ID {order_id} not found.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_PENDING:
                order.status = Order.STATUS_CONFIRMED
            else:
                print(f"Order {order_id} is not in PENDING state to be confirmed.")
        else:
            print(f"Order with ID {order_id} not found.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order:
            if order.status == Order.STATUS_CONFIRMED:
                order.status = Order.STATUS_SHIPPED
            else:
                print(f"Order {order_id} is not in CONFIRMED state to be shipped.")
        else:
            print(f"Order with ID {order_id} not found.")


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

# 주문 확인
order_manager.confirm_order(1)

# 주문 배송
order_manager.ship_order(1)

# 주문 목록 (배송 후)
all_orders = order_manager.list_orders()
for order in all_orders:
    print(order)

# 할인 적용
order_manager.apply_discount(2, 0.1)  # 10% 할인

# 주문 총액 조회
total = order_manager.get_order_total(2)
if total is not None:
    print(f"Order 2 total: {total:.2f}")

# 주문 취소 (try/except 블록 사용)
try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(e)

# 주문 목록 (취소 후)
all_orders = order_manager.list_orders()
for order in all_orders:
    print(order)

# 잘못된 상태에서 취소 시도
try:
    order_manager.cancel_order(2)
except ValueError as e:
    print(e)