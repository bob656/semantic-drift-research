from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int

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

class Inventory:
    def __init__(self):
        self.items: dict[str, Item] = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        """상품을 재고에 등록합니다."""
        if item_name in self.items:
            print(f"오류: 상품 {item_name}이 이미 존재합니다.")
            return
        new_item = Item(item_name, price, 1, stock)
        self.items[item_name] = new_item
        print(f"상품 {item_name}이 재고에 추가되었습니다.")

    def get_stock(self, item_name: str) -> int:
        """현재 재고 수량을 반환합니다."""
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"오류: 상품 {item_name}이 존재하지 않습니다.")
            return 0

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        """재고를 차감합니다. 부족 시 ValueError를 발생시킵니다."""
        item = self.items.get(item_name)
        if not item:
            raise ValueError(f"오류: 상품 {item_name}이 존재하지 않습니다.")
        if item.stock < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        item.stock -= quantity
        print(f"상품 {item_name} 재고가 {quantity}만큼 차감되었습니다.")

class OrderManager:
    def __init__(self):
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}

    def add_order(self, order_id: int, items: list[Item], inventory: Inventory) -> None:
        """주문을 추가합니다."""
        if order_id in self.orders:
            print(f"오류: 주문 ID {order_id}가 이미 존재합니다.")
            return

        total = sum(item.price * item.quantity for item in items)
        new_order = Order(order_id, items)
        new_order.total = total
        self.orders[order_id] = new_order
        print(f"주문 {order_id}가 추가되었습니다.")

        # 재고 차감
        for item in items:
            try:
                inventory.reduce_stock(item.name, item.quantity)
            except ValueError as e:
                print(e)
                # 주문 취소 로직 구현 필요 (간단하게는 여기서 return)
                return

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
                print(f"오류: 주문 {order_id}는 아직 확인되지 않았습니다.")
        else:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        """결제를 처리합니다."""
        order = self.get_order(order_id)
        if not order:
            print(f"오류: 주문 ID {order_id}가 존재하지 않습니다.")
            return None

        if order.total != amount:
            raise ValueError(f"결제 금액이 일치하지 않습니다. 주문 금액: {order.total}, 결제 금액: {amount}")

        payment = Payment(len(self.payments) + 1, order_id, amount, method)
        self.payments[payment.payment_id] = payment
        print(f"결제가 완료되었습니다. 결제 ID: {payment.payment_id}")
        return payment

    def get_payment(self, payment_id: int) -> Payment | None:
        """결제 정보를 조회합니다."""
        return self.payments.get(payment_id)


# Example Usage
inventory = Inventory()
inventory.add_item("Laptop", 1200.00, 5)
inventory.add_item("Mouse", 25.00, 10)

order_manager = OrderManager()
items = [
    Item("Laptop", 1200.00, 1, 0),
    Item("Mouse", 25.00, 1, 0)
]
order_manager.add_order(1, items, inventory)

print(inventory.get_stock("Laptop"))
print(inventory.get_stock("Mouse"))

try:
    order_manager.add_order(2, [Item("Keyboard", 75.00, 1, 0)], inventory)
except ValueError as e:
    print(e)