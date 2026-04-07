from dataclasses import dataclass, field

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id, items, discount_percent=0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items: list[Item], discount_percent=0.0):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items, discount_percent)
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
        return [(order.order_id, [f'{item.name} x{item.quantity}' for item in order.items], order.total) for order in self.orders.values()]

    def apply_discount(self, order_id, discount_percent):
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
                print(f"Order ID {order_id} updated with discount {discount_percent*100}%.")
            else:
                print(f"Order ID {order_id} not found.")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id):
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()

    # 주문 추가
    item1 = Item("item1", 25.0, 2)
    item2 = Item("item2", 10.0, 1)
    manager.add_order(1, [item1, item2])

    item3 = Item("item3", 20.0, 1)
    manager.add_order(2, [item3])

    # 할인 적용
    manager.apply_discount(1, 0.1)

    # 주문 조회 및 총액 확인
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}")

    # 모든 주문 목록
    all_orders = manager.list_orders()
    for order_id, items, total in all_orders:
        print(f"Order {order_id}: Items - {items}, Total - {total}")

    # 특정 주문의 총액 확인
    print("Order 1 total:", manager.get_order_total(1))

    # 주문 취소
    manager.cancel_order(1)

    # 취소된 후 다시 조회
    canceled_order = manager.get_order(1)
    if not canceled_order:
        print("Order 1 has been canceled.")