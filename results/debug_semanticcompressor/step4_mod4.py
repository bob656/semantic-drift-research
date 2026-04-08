from typing import List, Optional, dataclass

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class OrderStatus:
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = OrderStatus.PENDING
        self.update_total()

    def update_total(self) -> None:
        total_price = sum(item.total_price for item in self.items)
        self.total = total_price * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        self.orders[order_id] = Order(order_id, items, discount_percent)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED
        else:
            raise ValueError("Invalid status to confirm an order")

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.SHIPPED
        else:
            raise ValueError("Invalid status to ship an order")

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.PENDING or order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.CANCELLED
        elif order.status == OrderStatus.SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order does not exist")
        if amount != order.total:
            raise ValueError("Payment amount does not match order total")

        payment_id = max(self.payments.keys(), default=0) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment

        order.status = OrderStatus.CONFIRMED
        return payment

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values()]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    items1 = [Item("Apple", 0.5, 2), Item("Banana", 0.3, 3)]
    manager.add_order(1, items1, discount_percent=0.1)
    
    items2 = [Item("Bread", 2.0, 1), Item("Milk", 1.5, 2)]
    manager.add_order(2, items2, discount_percent=0.2)
    
    # 결제 처리
    payment = manager.process_payment(1, order.total, method="Credit Card")
    print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    
    # 주문 확인
    try:
        manager.confirm_order(1)
        print("Order confirmed")
    except ValueError as e:
        print(e)

    # 주문 배송
    try:
        manager.ship_order(1)
        print("Order shipped")
    except ValueError as e:
        print(e)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")
    
    # 모든 주문 목록 출력
    orders = manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")
    
    # 주문 취소
    try:
        manager.cancel_order(1)
        print("Order cancelled")
    except ValueError as e:
        print(e)

    # 이미 취소된 주문을 다시 취소하려고 시도
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)