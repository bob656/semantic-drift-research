import datetime

class Item:
    """아이템 클래스"""

    def __init__(self, name, price, quantity, stock):
        """
        아이템 객체를 초기화합니다.

        Args:
            name (str): 아이템 이름.
            price (float): 아이템 가격.
            quantity (int): 아이템 수량.
            stock (int): 현재 재고 수량.
        """
        self.name = name
        self.price = price
        self.quantity = quantity
        self.stock = stock

    def __repr__(self):
        """아이템 객체의 문자열 표현을 반환합니다."""
        return f"Item(name={self.name}, price={self.price}, quantity={self.quantity}, stock={self.stock})"


class Order:
    """주문 클래스"""

    def __init__(self, order_id, items, total, discount_percent=0.0, status="PENDING", customer_id=None):
        """
        주문 객체를 초기화합니다.

        Args:
            order_id (int): 주문 ID.
            items (list of Item): 주문 항목 목록.
            total (float): 주문 총액.
            discount_percent (float): 할인율 (0.0~1.0).
            status (str): 주문 상태.
            customer_id (int): 고객 ID.
        """
        self.order_id = order_id
        self.items = items
        self.total = total
        self.discount_percent = discount_percent
        self.status = status
        self.created_at = datetime.datetime.now()  # 주문 생성 시각
        self.customer_id = customer_id

    def __repr__(self):
        """주문 객체의 문자열 표현을 반환합니다."""
        return (
            f"Order(order_id={self.order_id}, items={self.items}, total={self.total}, discount_percent={self.discount_percent}, status={self.status}, created_at={self.created_at}, customer_id={self.customer_id})"
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
        self.refunded = False  # 새 필드: 환불 여부

    def __repr__(self):
        """결제 객체의 문자열 표현을 반환합니다."""
        return f"Payment(payment_id={self.payment_id}, order_id={self.order_id}, amount={self.amount}, method={self.method}, refunded={self.refunded})"


class Inventory:
    """재고 관리 클래스"""

    def __init__(self):
        """재고 관리 객체를 초기화합니다."""
        self.items = {}  # 아이템 이름 -> Item 객체

    def add_item(self, item_name, price, stock):
        """
        새로운 아이템을 재고에 추가합니다.

        Args:
            item_name (str): 아이템 이름.
            price (float): 아이템 가격.
            stock (int): 초기 재고 수량.
        """
        if item_name in self.items:
            print(f"오류: 이미 {item_name}이 재고에 있습니다.")
            return
        item = Item(item_name, price, 1, stock)
        self.items[item_name] = item
        print(f"{item_name}을(를) 재고에 추가했습니다.")

    def get_stock(self, item_name):
        """
        아이템의 현재 재고 수량을 반환합니다.

        Args:
            item_name (str): 아이템 이름.

        Returns:
            int: 현재 재고 수량. 아이템이 없으면 -1을 반환합니다.
        """
        if item_name in self.items:
            return self.items[item_name].stock
        else:
            print(f"{item_name}을(를) 찾을 수 없습니다.")
            return -1

    def reduce_stock(self, item_name, quantity):
        """
        아이템의 재고를 감소시킵니다.

        Args:
            item_name (str): 아이템 이름.
            quantity (int): 감소시킬 수량.

        Raises:
            ValueError: 재고가 부족한 경우.
        """
        if item_name not in self.items:
            raise ValueError(f"{item_name}을(를) 찾을 수 없습니다.")

        if self.items[item_name].stock < quantity:
            raise ValueError(f"{item_name}의 재고가 부족합니다.")

        self.items[item_name].stock -= quantity
        print(f"{item_name}의 재고를 {quantity}만큼 감소시켰습니다.")


class Customer:
    """고객 클래스"""
    def __init__(self, customer_id, name, email):
        self.customer_id = customer_id
        self.name = name
        self.email = email

    def __repr__(self):
        return f"Customer(customer_id={self.customer_id}, name={self.name}, email={self.email})"


class OrderManager:
    def __init__(self):
        self.orders = {}
        self.customers = {}
        self.inventory = Inventory()

    def add_customer(self, customer_id, name, email):
        """고객 등록"""
        if customer_id in self.customers:
            print(f"오류: 이미 고객 {customer_id}가 등록되어 있습니다.")
            return
        self.customers[customer_id] = Customer(customer_id, name, email)
        print(f"고객 {name} ({email})을(를) 등록했습니다.")

    def get_customer(self, customer_id):
        """고객 정보 반환"""
        return self.customers.get(customer_id)

    def get_orders_by_customer(self, customer_id):
        """특정 고객의 모든 주문 반환"""
        customer = self.get_customer(customer_id)
        if not customer:
            print(f"고객 {customer_id}을(를) 찾을 수 없습니다.")
            return []
        return [order for order in self.orders.values() if order.customer_id == customer_id]

    def add_order(self, order_id, items, inventory, customer_id):
        """주문 추가"""
        if customer_id not in self.customers:
            raise ValueError(f"등록되지 않은 고객 ID: {customer_id}")

        order = Order(order_id, items, 0, status="PENDING", customer_id=customer_id)
        self.orders[order_id] = order
        print(f"주문 {order_id}을(를) 고객 {customer_id}에 추가했습니다.")
        return order

    def get_order(self, order_id):
        """주문 정보 반환"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        """주문 상태를 취소합니다."""
        order = self.get_order(order_id)
        if order:
            order.status = "CANCELLED"
            print(f"주문 {order_id}가 취소되었습니다.")
        else:
            print(f"주문 {order_id}을(를) 찾을 수 없습니다.")

    def apply_discount(self, order_id, discount_percent):
        """할인 적용"""
        order = self.get_order(order_id)
        if order:
            order.discount_percent = discount_percent
            order.total -= order.total * discount_percent / 100
            print(f"주문 {order_id}에 {discount_percent}% 할인을 적용했습니다.")
        else:
            print(f"주문 {order_id}을(를) 찾을 수 없습니다.")

    def get_order_total(self, order_id):
        """주문 총액 반환"""
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"주문 {order_id}을(를) 찾을 수 없습니다.")
            return None

    def confirm_order(self, order