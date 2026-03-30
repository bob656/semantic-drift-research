import datetime

class OrderManager:
    """
    주문 데이터 저장소를 관리하는 클래스입니다.
    """
    def __init__(self, inventory):
        """
        OrderManager 객체를 초기화합니다.
        """
        self.orders = {}  # 주문 데이터를 저장할 딕셔너리 (order_id: Order)
        self.payments = {} # 결제 데이터를 저장할 딕셔너리 (payment_id: Payment)
        self.next_payment_id = 1
        self.inventory = inventory

    def add_order(self, order_id, items):
        """
        주문을 추가합니다.

        Args:
            order_id (int): 주문 ID
            items (list[Item]): 주문 항목 목록

        Raises:
            ValueError: order_id가 중복된 경우
            TypeError: items가 Item 객체 목록이 아닌 경우
        """
        if not isinstance(order_id, int):
            raise TypeError("order_id must be an integer")
        if not isinstance(items, list):
            raise TypeError("items must be a list")
        if not all(isinstance(item, Item) for item in items):
            raise TypeError("items must be a list of Item objects")

        if order_id in self.orders:
            raise ValueError(f"Order ID {order_id} already exists")

        for item in items:
            self.inventory.reduce_stock(item.name, item.quantity)

        order = Order(order_id, items)
        self.orders[order_id] = order

    def get_order(self, order_id):
        """
        주문 ID를 기반으로 주문을 조회합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            Order | None: 주문 객체. 주문이 없으면 None을 반환합니다.
        """
        return self.orders.get(order_id)

    def confirm_order(self, order_id):
        """
        주문 상태를 PENDING에서 CONFIRMED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"

    def ship_order(self, order_id):
        """
        주문 상태를 CONFIRMED에서 SHIPPED로 변경합니다.
        """
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"

    def cancel_order(self, order_id):
        """
        주문 상태를 CANCELLED로 변경합니다.
        """
        order = self.get_order(order_id)
        if not order:
            return

        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

        order.status = "CANCELLED"

    def list_orders(self):
        """
        모든 주문 목록을 반환합니다.
        """
        return [(order_id, order) for order_id, order in self.orders.items()]

    def apply_discount(self, order_id, discount_percent):
        """
        주문에 할인율을 적용합니다.

        Args:
            order_id (int): 주문 ID
            discount_percent (float): 할인율 (0.0 ~ 1.0)

        Raises:
            ValueError: order_id가 존재하지 않거나 discount_percent가 범위를 벗어난 경우
        """
        if order_id not in self.orders:
            raise ValueError(f"Order ID {order_id} does not exist")
        if not 0.0 <= discount_percent <= 1.0:
            raise ValueError("Discount percent must be between 0.0 and 1.0")

        order = self.orders[order_id]
        order.discount_percent = discount_percent
        order.total = order.calculate_total()

    def get_order_total(self, order_id):
        """
        주문의 총액을 반환합니다.

        Args:
            order_id (int): 주문 ID

        Returns:
            float: 주문의 총액
        """
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            return 0.0

    def process_payment(self, order_id, amount, method):
        """
        결제를 처리하고 Payment 객체를 반환합니다.

        Args:
            order_id (int): 주문 ID
            amount (float): 결제 금액
            method (str): 결제 방법

        Returns:
            Payment: Payment 객체

        Raises:
            ValueError: 주문이 존재하지 않거나 결제 금액이 주문 총액과 일치하지 않는 경우
        """
        order = self.get_order(order_id)
        if not order:
            raise ValueError(f"Order ID {order_id} does not exist")

        if abs(amount - order.total) > 0.001:  # 부동소수점 비교를 위해 오차 허용
            raise ValueError(f"Payment amount {amount} does not match order total {order.total}")

        payment = Payment(self.next_payment_id, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        self.next_payment_id += 1
        order.status = "CONFIRMED"  # 결제 성공 시 주문 상태를 CONFIRMED로 변경
        return payment

    def get_payment(self, payment_id):
        """
        결제 ID를 기반으로 결제 정보를 조회합니다.

        Args:
            payment_id (int): 결제 ID

        Returns:
            Payment | None: 결제 객체. 결제가 없으면 None을 반환합니다.
        """
        return self.payments.get(payment_id)

    def get_order_history(self):
        """
        모든 주문 내역을 반환합니다 (취소 주문 포함).
        """
        return sorted([(order_id, order) for order_id, order in self.orders.items()],
                      key=lambda item: item[1].created_at, reverse=True)

    def get_orders_by_status(self, status):
        """
        지정된 상태의 주문 목록을 반환합니다.

        Args:
            status (str): 주문 상태 ("PENDING", "CONFIRMED", "SHIPPED", "CANCELLED")

        Returns:
            list[tuple[int, Order]]: 지정된 상태의 주문 목록
        """
        return [(order_id, order) for order_id, order in self.orders.items() if order.status == status]

class Item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = items
        self.discount_percent = 0.0
        self.total = self.calculate_total()
        self.status = "PENDING"
        self.created_at = datetime.datetime.now()

    def calculate_total(self):
        """
        주문 항목의 총 가격을 계산합니다.
        """
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total * (1 - self.discount_percent)

class Payment:
    def __init__(self, payment_id, order_id, amount, method):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.method = method

class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, stock):
        self.items[item_name] = {'price': price, 'stock': stock}

    def get_stock(self, item_name):
        return self.items.get(item_name, {}).get('stock', 0)

    def reduce_stock(self, item_name, quantity):
        if item_name not in self.items or self.items[item_name]['stock'] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name]['stock'] -= quantity