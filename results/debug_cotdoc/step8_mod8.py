import datetime

class Item:
    """주문 품목을 나타내는 클래스입니다."""

    def __init__(self, name, price, quantity, stock):
        """
        품목 객체를 초기화합니다.

        Args:
            name (str): 품목 이름.
            price (float): 품목 가격.
            quantity (int): 품목 수량.
            stock (int): 현재 재고 수량.
        """
        self.name = name
        self.price = price
        self.quantity = quantity
        self.stock = stock

    def __repr__(self):
        """품목 객체의 문자열 표현을 반환합니다."""
        return f"Item(name={self.name}, price={self.price}, quantity={self.quantity}, stock={self.stock})"


class Order:
    """주문을 나타내는 클래스입니다."""

    def __init__(self, order_id, items, total, discount_percent=0.0, status="PENDING", customer_id=None):
        """
        주문 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문에 포함된 품목 목록.
            total (float): 주문 총액.
            discount_percent (float): 할인율 (0.0 ~ 1.0). 기본값은 0.0입니다.
            status (str): 주문 상태. 기본값은 "PENDING"입니다.
            customer_id (int): 고객 ID.
        """
        self.order_id = order_id
        self.items = items
        self.total = total
        self.discount_percent = discount_percent
        self.status = status
        self.created_at = datetime.datetime.now()
        self.customer_id = customer_id

    def __repr__(self):
        """주문 객체의 문자열 표현을 반환합니다."""
        return f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, discount_percent={self.discount_percent}, status={self.status}, created_at={self.created_at}, customer_id={self.customer_id})"


class Payment:
    """결제를 나타내는 클래스입니다."""

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
        self.refunded = False  # 새 필드

    def __repr__(self):
        """결제 객체의 문자열 표현을 반환합니다."""
        return f"Payment(payment_id={self.payment_id}, order_id={self.order_id}, amount={self.amount}, method={self.method}, refunded={self.refunded})"


class Inventory:
    """재고를 관리하는 클래스입니다."""

    def __init__(self):
        self.items = {}  # 품목 이름 -> Item 객체

    def add_item(self, item_name, price, stock):
        """상품을 재고에 등록합니다."""
        if item_name in self.items:
            print(f"오류: 이미 {item_name}이(가) 재고에 있습니다.")
            return
        item = Item(item_name, price, 0, stock)  # 수량은 0으로 초기화
        self.items[item_name] = item
        print(f"{item_name}을(를) 재고에 추가했습니다. 현재 재고: {stock}")

    def get_stock(self, item_name):
        """현재 재고 수량을 반환합니다."""
        if item_name in self.items:
            return self.items[item_name].stock
        else:
            print(f"{item_name}이(가) 재고에 없습니다.")
            return None

    def reduce_stock(self, item_name, quantity):
        """재고를 차감합니다. 부족 시 ValueError를 발생시킵니다."""
        if item_name not in self.items:
            print(f"{item_name}이(가) 재고에 없습니다.")
            return

        if self.items[item_name].stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")

        self.items[item_name].stock -= quantity
        print(f"{item_name} 재고를 {quantity}만큼 차감했습니다. 현재 재고: {self.items[item_name].stock}")


class Customer:
    """고객을 나타내는 클래스입니다."""

    def __init__(self, customer_id, name, email):
        """
        고객 객체를 초기화합니다.

        Args:
            customer_id (int): 고객 ID.
            name (str): 고객 이름.
            email (str): 고객 이메일.
        """
        self.customer_id = customer_id
        self.name = name
        self.email = email

    def __repr__(self):
        return f"Customer(customer_id={self.customer_id}, name={self.name}, email={self.email})"


class OrderManager:
    def __init__(self):
        self.customers = {}
        self.orders = {}
        self.payments = {}

    def add_customer(self, customer_id, name, email):
        """고객 등록"""
        if customer_id in self.customers:
            raise ValueError(f"이미 등록된 고객 ID: {customer_id}")
        self.customers[customer_id] = Customer(customer_id, name, email)
        print(f"고객 {name} ({customer_id}) 등록됨")

    def get_customer(self, customer_id):
        """고객 정보 반환"""
        if customer_id not in self.customers:
            return None
        return self.customers[customer_id]

    def get_orders_by_customer(self, customer_id):
        """특정 고객의 모든 주문 반환"""
        orders = []
        for order_id, order in self.orders.items():
            if order.customer_id == customer_id:
                orders.append(order)
        return orders

    def add_order(self, order_id, items, inventory, customer_id):
        """주문 추가"""
        if customer_id not in self.customers:
            raise ValueError(f"등록되지 않은 고객 ID: {customer_id}")

        total = sum(item.price * item.quantity for item in items)
        order = Order(order_id, items, total, customer_id=customer_id)
        self.orders[order_id] = order
        print(f"주문 {order_id} 추가됨, 고객 ID: {customer_id}")

    def get_order(self, order_id):
        """주문 정보 반환"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        """주문 취소"""
        order = self.get_order(order_id)
        if order:
            order.status = "CANCELLED"
            print(f"주문 {order_id} 취소됨")

    def apply_discount(self, order_id, discount_percent):
        """할인 적용"""
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total *= (1 - discount_percent)
            print(f"주문 {order_id}에 {discount_percent * 100}% 할인 적용됨")

    def get_order_total(self, order_id):
        """주문 총액 반환"""
        order = self.get_order(order_id)
        return order.total if order else None

    def confirm_order(self, order_id):
        """주문 상태를 확인으로 변경"""
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"주문 {order_id}이(가) 확인되었습니다.")
        elif order and order.status != "PENDING":
            print(f"주문 {order_id}은 이미 {order.status} 상태입니다.")
        else:
            print(f"주문 {order_id}을 찾을 수 없습니다.")

    def ship_order(self, order_id):
        """