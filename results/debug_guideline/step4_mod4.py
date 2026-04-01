from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

@dataclass
class Order:
    order_id: int
    items: list[Item]
    discount_percent: float = 0.0
    total: float = 0.0
    status: str = "PENDING"

@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class OrderManager:
    def __init__(self):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}

    def add_order(self, order_id: int, items: list[Item]) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return

        total = sum(item.price * item.quantity for item in items)
        new_order = Order(order_id, items)
        new_order.total = total
        self.orders[order_id] = new_order
        print(f"주문 {order_id}가 추가되었습니다.")

    def get_order(self, order_id: int) -> Order | None:
        """주문 ID로 주문을 조회합니다. 없으면 None을 반환합니다."""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        """주문 ID로 주문을 취소합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return

        if order.status in ("SHIPPED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        if order.status in ("PENDING", "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"주문 {order_id}가 취소되었습니다.")
        else:
            print(f"오류: 주문 ID {order_id}는 이미 취소되었거나 배송 중입니다.")

    def list_orders(self) -> list[Order]:
        """모든 주문 목록을 반환합니다."""
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        """주문에 할인을 적용합니다."""
        if not 0.0 <= discount_percent <= 1.0:
            print(f"오류: 할인율은 0.0과 1.0 사이의 값이어야 합니다.")
            return

        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
            print(f"주문 {order_id}에 {discount_percent * 100}% 할인이 적용되었습니다.")
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")

    def get_order_total(self, order_id: int) -> float:
        """주문 ID로 주문의 총액을 조회합니다."""
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return 0.0

    def confirm_order(self, order_id: int) -> None:
        """주문 상태를 PENDING에서 CONFIRMED로 변경합니다."""
        order = self.get_order(order_id)
        if order:
            if order.status == "PENDING":
                order.status = "CONFIRMED"
                print(f"주문 {order_id}가 확인되었습니다.")
            else:
                print(f"오류: 주문 {order_id}는 이미 {order.status} 상태입니다.")
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")

    def ship_order(self, order_id: int) -> None:
        """주문 상태를 CONFIRMED에서 SHIPPED로 변경합니다."""
        order = self.get_order(order_id)
        if order:
            if order.status == "CONFIRMED":
                order.status = "SHIPPED"
                print(f"주문 {order_id}가 배송되었습니다.")
            else:
                print(f"오류: 주문 {order_id}는 이미 {order.status} 상태입니다.")
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        """결제를 처리합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return None

        if abs(amount - order.total) > 0.01:  # 부동 소수점 비교 문제 해결
            raise ValueError(f"오류: 결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment_id = max(self.payments.keys(), default=0) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "CONFIRMED"
        print(f"주문 {order_id} 결제가 성공적으로 처리되었습니다.")
        return payment

    def get_payment(self, order_id: int) -> Payment | None:
        """주문 ID로 결제 정보를 조회합니다."""
        for payment in self.payments.values():
            if payment.order_id == order_id:
                return payment
        return None


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    order_manager.add_order(1, [Item("노트북", 800.00, 1), Item("마우스", 30.00, 1)])
    order_manager.add_order(2, [Item("키보드", 100.00, 1), Item("모니터", 400.00, 1)])

    # 주문 조회
    order1 = order_manager.get_order(1)
    if order1:
        print(f"주문 1: {order1}")
    else:
        print("주문 1을 찾을 수 없습니다.")

    order3 = order_manager.get_order(3)
    if order3:
        print(f"주문 3: {order3}")
    else:
        print("주문 3을 찾을 수 없습니다.")

    # 주문 목록
    all_orders = order_manager.list_orders()
    print("\n모든 주문:")
    for order in all_orders:
        print(order)

    # 주문 확인
    order_manager.confirm_order(1)

    # 주문 배송
    order_manager.ship_order(1)

    # 주문 목록 (배송 후)
    all_orders = order_manager.list_orders()
    print("\n배송 후 모든 주문:")
    for order in all_orders:
        print(order)

    # 결제 처리
    payment1 = order_manager.process_payment(1, 830.00, "credit_card")
    if payment1:
        print(f"결제 정보: {payment1}")

    # 결제 정보 조회
    payment_info = order_manager.get_payment(1)
    if payment_info:
        print(f"주문 1의 결제 정보: {payment_info}")

    # 잘못된 결제 금액 처리
    try:
        order_manager.process_payment(2, 500.00, "paypal")
    except ValueError as e:
        print(e)