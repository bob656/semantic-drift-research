from dataclasses import dataclass, field

@dataclass
class Item:
    name: str
    price: float
    quantity: int

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class Order:
    def __init__(self, order_id, items, discount_percent=0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = "PENDING"
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id, items: list[Item], discount_percent=0.0):
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items, discount_percent)
            print(f"Order ID {order_id} added.")

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def confirm_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print("Order cannot be confirmed.")

    def ship_order(self, order_id):
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print("Order cannot be shipped.")

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def list_orders(self):
        return [(order.order_id, [f'{item.name} x{item.quantity}' for item in order.items], order.total, order.status) for order in self.orders.values()]

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

    def process_payment(self, order_id, amount, method):
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if amount == order.total:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id, order_id, amount, method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} confirmed and paid.")
                return payment
            else:
                raise ValueError("Payment amount does not match the order total.")
        else:
            print("Order cannot be processed for payment.")

    def get_payment(self, order_id):
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        print(f"Payment for Order ID {order_id} not found.")
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

    # 결제 처리
    try:
        payment = manager.process_payment(1, 58.0, "Credit Card")
        print(f"Payment ID {payment.payment_id} processed for Order ID {payment.order_id}.")
    except ValueError as e:
        print(e)

    # 주문 상태 변경
    manager.confirm_order(2)  # 수동 확인

    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 주문 조회 및 총액 확인
    order = manager.get_order(1)
    if order:
        print(f"Order {order.order_id}: Items - {[f'{item.name} x{item.quantity}' for item in order.items]}, Total - {order.total}, Status - {order.status}")

    # 결제 정보 조회
    payment = manager.get_payment(1)
    if payment:
        print(f"Payment ID {payment.payment_id} for Order ID {payment.order_id}: Amount - {payment.amount}, Method - {payment.method}")

    # 모든 주문 목록
    all_orders = manager.list_orders()
    for order_id, items, total, status in all_orders:
        print(f"Order {order_id}: Items - {items}, Total - {total}, Status - {status}")

    # 특정 주문의 총액 확인
    print("Order 1 total:", manager.get_order_total(1))