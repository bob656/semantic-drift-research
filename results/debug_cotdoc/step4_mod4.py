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

    def __init__(self, order_id, items, total, discount_percent=0.0, status="PENDING"):
        """
        주문 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문 항목 목록.
            total (float): 주문 총액.
            discount_percent (float): 할인율 (0.0~1.0).
            status (str): 주문 상태.
        """
        self.order_id = order_id
        self.items = items
        self.total = total
        self.discount_percent = discount_percent
        self.status = status

    def __repr__(self):
        """주문 객체의 문자열 표현을 반환합니다."""
        return (
            f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, discount_percent={self.discount_percent}, status={self.status})"
        )


class Payment:
    """결제 클래스"""

    def __init__(self, payment_id, order_id, amount, method):
        """
        결제 객체를 초기화합니다.

        Args:
            payment_id (int): 결제 ID.
            order_id (int): 주문 ID.
            amount (float): 결제 금액.
            method (str): 결제 방법.
        """
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method

    def __repr__(self):
        """결제 객체의 문자열 표현을 반환합니다."""
        return f"Payment(payment_id={self.payment_id}, order_id={self.order_id}, amount={self.amount}, method={self.method})"


class OrderManager:
    """주문 관리 클래스"""

    def __init__(self):
        """주문 관리 객체를 초기화합니다."""
        self.orders = {}  # 주문 ID를 키로, 주문 객체를 값으로 하는 딕셔너리
        self.payments = {} # 결제 ID를 키로, 결제 객체를 값으로 하는 딕셔너리

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
        order = self.get_order(order_id)
        if order:
            if order.status in ("PENDING", "CONFIRMED"):
                order.status = "CANCELLED"
                print(f"주문 {order_id}가 취소되었습니다.")
            elif order.status == "SHIPPED":
                raise ValueError("배송 중인 주문은 취소할 수 없습니다")
            else:
                print(f"주문 {order_id}는 이미 {order.status} 상태입니다.")
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
        """
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total = order.total * (1 - discount_percent)
            print(f"주문 {order_id}에 {discount_percent * 100}% 할인이 적용되었습니다.")
        else:
            print(f"주문 ID {order_id}를 찾을 수 없습니다.")

    def get_order_total(self, order_id):
        """
        주문의 총액을 반환합니다.

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

    def confirm_order(self, order_id):
        """
        주문 상태를 PENDING에서 CONFIRMED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"주문 {order_id}가 확인되었습니다.")
        elif order:
            print(f"주문 {order_id}는 이미 {order.status} 상태입니다.")
        else:
            print(f"주문 ID {order_id}를 찾을 수 없습니다.")

    def ship_order(self, order_id):
        """
        주문 상태를 CONFIRMED에서 SHIPPED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"주문 {order_id}가 배송되었습니다.")
        elif order:
            print(f"주문 {order_id}는 이미 {order.status} 상태입니다.")
        else:
            print(f"주문 ID {order_id}를 찾을 수 없습니다.")

    def process_payment(self, order_id, amount, method):
        """
        결제를 처리합니다.

        Args:
            order_id (int): 주문 ID.
            amount (float): 결제 금액.
            method (str): 결제 방법.

        Returns:
            Payment: 결제 객체.
        """
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"주문 ID {order_id}를 찾을 수 없습니다.")

        if order.total != amount:
            raise ValueError(f"결제 금액이 주문 총액과 일치하지 않습니다. 주문 총액: {order.total}, 결제 금액: {amount}")

        payment_id = len(self.payments) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment
        order.status = "CONFIRMED"
        print(f"주문 {order_id} 결제가 성공적으로 처리되었습니다. 결제 방법: {method}")
        return payment

    def get_payment(self, order_id):
        """
        해당 주문의 결제 정보를 반환합니다.

        Args:
            order_id (int): 주문