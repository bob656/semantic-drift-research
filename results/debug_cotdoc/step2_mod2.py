class Item:
    """아이템 클래스"""

    def __init__(self, name, price, quantity):
        """
        아이템 객체를 초기화합니다.

        Args:
            name (str): 아이템 이름.
            price (float): 아이템 가격.
            quantity (int): 아이템 수량.
        """
        self.name = name
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        """아이템 객체의 문자열 표현을 반환합니다."""
        return f"Item(name={self.name}, price={self.price}, quantity={self.quantity})"


class Order:
    """주문 클래스"""

    def __init__(self, order_id, items, total, discount_percent=0.0):
        """
        주문 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문 항목 목록.
            total (float): 주문 총액.
            discount_percent (float): 할인율 (0.0~1.0).
        """
        self.order_id = order_id
        self.items = items
        self.total = total
        self.discount_percent = discount_percent

    def __repr__(self):
        """주문 객체의 문자열 표현을 반환합니다."""
        return (
            f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, discount_percent={self.discount_percent})"
        )


class OrderManager:
    """주문 관리 클래스"""

    def __init__(self):
        """주문 관리 객체를 초기화합니다."""
        self.orders = {}  # 주문 ID를 키로, 주문 객체를 값으로 하는 딕셔너리

    def add_order(self, order_id, items, total):
        """
        주문을 추가합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문 항목 목록.
            total (float): 주문 총액.
        """
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return

        # total을 계산된 값으로 대체
        calculated_total = sum(item.price * item.quantity for item in items)
        new_order = Order(order_id, items, calculated_total)
        self.orders[order_id] = new_order
        print(f"주문 {order_id}가 추가되었습니다.")

    def get_order(self, order_id):
        """
        주문 ID를 기준으로 주문을 조회합니다.

        Args:
            order_id (int): 주문 ID.

        Returns:
            Order: 주문 객체. 주문이 없으면 None을 반환합니다.
        """
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            print(f"주문 ID {order_id}를 찾을 수 없습니다.")
            return None

    def cancel_order(self, order_id):
        """
        주문 ID를 기준으로 주문을 취소합니다.

        Args:
            order_id (int): 주문 ID.
        """
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"주문 {order_id}가 취소되었습니다.")
        else:
            print(f"주문 ID {order_id}를 찾을 수 없습니다.")

    def list_orders(self):
        """
        모든 주문 목록을 반환합니다.

        Returns:
            list of Order: 주문 객체 목록.
        """
        if not self.orders:
            print("주문이 없습니다.")
            return []
        else:
            return list(self.orders.values())

    def apply_discount(self, order_id, discount_percent):
        """
        주문에 할인율을 적용합니다.

        Args:
            order_id (int): 주문 ID.
            discount_percent (float): 할인율 (0.0~1.0).
        """
        if not 0.0 <= discount_percent <= 1.0:
            print("오류: 할인율은 0.0과 1.0 사이의 값이어야 합니다.")
            return

        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = sum(item.price * item.quantity for item in order.items) * (1 - order.discount_percent)
            print(f"주문 {order_id}에 {discount_percent * 100}% 할인이 적용되었습니다.")

    def get_order_total(self, order_id):
        """
        주문 ID를 기준으로 주문의 총액을 반환합니다.

        Args:
            order_id (int): 주문 ID.

        Returns:
            float: 주문 총액. 주문이 없으면 None을 반환합니다.
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return None


# 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()

    # 주문 추가
    item1 = Item("상품 A", 10.0, 2)
    item2 = Item("상품 B", 5.0, 3)
    order_manager.add_order(1, [item1, item2], 0.0)  # total 파라미터는 의미 없음

    item3 = Item("상품 C", 7.0, 1)
    order_manager.add_order(2, [item3], 0.0)

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

    # 할인 적용
    order_manager.apply_discount(1, 0.1)

    # 할인 적용 후 주문 목록
    all_orders = order_manager.list_orders()
    print(f"할인 적용 후 모든 주문: {all_orders}")

    # 총액 조회
    total = order_manager.get_order_total(1)
    if total is not None:
        print(f"주문 1 총액: {total}")