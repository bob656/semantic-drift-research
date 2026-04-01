class Item:
    """주문 품목을 나타내는 클래스입니다."""

    def __init__(self, name, price, quantity):
        """
        품목 객체를 초기화합니다.

        Args:
            name (str): 품목 이름.
            price (float): 품목 가격.
            quantity (int): 품목 수량.
        """
        self.name = name
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        """품목 객체의 문자열 표현을 반환합니다."""
        return f"Item(name={self.name}, price={self.price}, quantity={self.quantity})"


class Order:
    """주문을 나타내는 클래스입니다."""

    def __init__(self, order_id, items, total):
        """
        주문 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문에 포함된 품목 목록.
            total (float): 주문 총액.
        """
        self.order_id = order_id
        self.items = items
        self.total = total

    def __repr__(self):
        """주문 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total})"


class OrderManager:
    """주문을 관리하는 클래스입니다."""

    def __init__(self):
        """OrderManager 객체를 초기화합니다."""
        self.orders = {}  # 주문 ID를 키로, Order 객체를 값으로 하는 딕셔너리

    def add_order(self, order_id, items, total):
        """주문을 추가합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문에 포함된 품목 목록.
            total (float): 주문 총액.
        """
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return
        order_total = 0
        for item in items:
            order_total += item.price * item.quantity
        order = Order(order_id, items, order_total)
        self.orders[order_id] = order
        print(f"주문 {order_id}이(가) 추가되었습니다.")

    def get_order(self, order_id):
        """주문 ID를 기반으로 주문을 조회합니다.

        Args:
            order_id (int): 조회할 주문 ID.

        Returns:
            Order: 주문 ID가 일치하는 Order 객체. 주문이 없으면 None을 반환합니다.
        """
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            print(f"주문 ID {order_id}을(를) 찾을 수 없습니다.")
            return None

    def cancel_order(self, order_id):
        """주문 ID를 기반으로 주문을 취소합니다.

        Args:
            order_id (int): 취소할 주문 ID.
        """
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"주문 {order_id}이(가) 취소되었습니다.")
        else:
            print(f"주문 ID {order_id}을(를) 찾을 수 없습니다.")

    def list_orders(self):
        """모든 주문 목록을 반환합니다.

        Returns:
            list of Order: 모든 Order 객체의 목록입니다.
        """
        if not self.orders:
            print("주문이 없습니다.")
            return []
        return list(self.orders.values())


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    items = [
        Item("노트북", 1200.00, 1),
        Item("마우스", 25.00, 1),
    ]
    order_manager.add_order(1, items, 0.00)

    items = [
        Item("키보드", 100.00, 1),
        Item("모니터", 400.00, 1),
    ]
    order_manager.add_order(2, items, 0.00)

    # 주문 조회
    order1 = order_manager.get_order(1)
    if order1:
        print(f"주문 1: {order1}")

    order3 = order_manager.get_order(3)  # 존재하지 않는 주문 조회

    # 모든 주문 목록
    all_orders = order_manager.list_orders()
    print(f"모든 주문: {all_orders}")

    # 주문 취소
    order_manager.cancel_order(2)

    # 취소 후 주문 목록
    all_orders = order_manager.list_orders()
    print(f"취소 후 모든 주문: {all_orders}")

    # 존재하지 않는 주문 취소
    order_manager.cancel_order(4)