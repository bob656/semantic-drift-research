from dataclasses import dataclass

@dataclass
class Order:
    order_id: int
    items: list[str]
    total: float

class OrderManager:
    def __init__(self):
        self.orders: dict[int, Order] = {}

    def add_order(self, order_id: int, items: list[str], total: float) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return
        new_order = Order(order_id, items, total)
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


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    order_manager.add_order(1, ["노트북", "마우스"], 1200.00)
    order_manager.add_order(2, ["키보드", "모니터"], 500.00)

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

    # 주문 취소
    order_manager.cancel_order(2)

    # 주문 목록 (취소 후)
    all_orders = order_manager.list_orders()
    print("\n취소 후 모든 주문:")
    for order in all_orders:
        print(order)

    # 존재하지 않는 주문 취소 시도
    order_manager.cancel_order(4)