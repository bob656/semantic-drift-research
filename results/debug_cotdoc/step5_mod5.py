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
            raise ValueError(f"재고 부족: {item_name}")

        self.items[item_name].stock -= quantity
        print(f"{item_name} 재고를 {quantity}만큼 감소시켰습니다. 현재 재고: {self.items[item_name].stock}")


class OrderManager:
    """주문 관리 클래스"""

    def __init__(self):
        """주문 관리 객체를 초기화합니다."""
        self.orders = {}
        self.payments = {}
        self.inventory = Inventory()  # Inventory 인스턴스 생성

    def add_order(self, order_id, items, inventory):
        """
        새로운 주문을 추가합니다.

        Args:
            order_id (int): 주문 ID.
            items (list): 주문 항목 목록.
            inventory (Inventory): 재고 관리 객체.
        """
        total = 0
        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                raise e
            total += item.price * item.quantity

        order = Order(order_id, items, total)
        self.orders[order_id] = order
        print(f"주문 {order_id}을(를) 추가했습니다.")

    def get_order(self, order_id):
        """
        주문 ID로 주문을 가져옵니다.
        """
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            return None

    def cancel_order(self, order_id):
        """
        주문을 취소합니다.
        """
        order = self.get_order(order_id)
        if order:
            for item in order.items:
                self.inventory.add_item(item.name, item.price, item.quantity)
            del self.orders[order_id]
            print(f"주문 {order_id}을(를) 취소했습니다.")
        else:
            print(f"주문 {order_id}을(를) 찾을 수 없습니다.")

    def list_orders(self):
        """
        모든 주문을 나열합니다.
        """
        for order_id, order in self.orders.items():
            print(f"주문 ID: {order_id}, 총액: {order.total}, 상태: {order.status}")

    def apply_discount(self, order_id, discount):
        """
        주문에 할인을 적용합니다.
        """
        order = self.get_order(order_id)
        if order:
            order.total -= discount
            print(f"주문 {order_id}에 {discount} 할인을 적용했습니다. 총액: {order.total}")
        else:
            print(f"주문 {order_id}을(를) 찾을 수 없습니다.")

    def get_order_total(self, order_id):
        """
        주문 총액을 가져옵니다.
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