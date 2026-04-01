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

class OrderManager:
    def __init__(self):
        self.orders: dict[int, Order] = {}

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
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"주문 {order_id}가 취소되었습니다.")
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")

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

    # 할인 적용
    order_manager.apply_discount(1, 0.1)

    # 주문 목록 (할인 적용 후)
    all_orders = order_manager.list_orders()
    print("\n할인 적용 후 모든 주문:")
    for order in all_orders:
        print(order)

    # 총액 조회
    total1 = order_manager.get_order_total(1)
    print(f"\n주문 1 총액: {total1}")

    # 주문 취소
    order_manager.cancel_order(2)

    # 주문 목록 (취소 후)
    all_orders = order_manager.list_orders()
    print("\n취소 후 모든 주문:")
    for order in all_orders:
        print(order)

    # 존재하지 않는 주문 취소 시도
    order_manager.cancel_order(4)