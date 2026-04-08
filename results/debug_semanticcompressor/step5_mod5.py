from typing import List, Optional, Dict

class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

class OrderStatus:
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

@dataclass
class Item:
    name: str
    price_per_unit: float
    quantity: int

class Inventory:
    def __init__(self):
        self.items: Dict[str, int] = {}

    def add_item(self, item_name: str, price_per_unit: float, stock: int) -> None:
        self.items[item_name] = (price_per_unit, stock)

    def get_stock(self, item_name: str) -> Optional[int]:
        return self.items.get(item_name, (0, 0))[1]

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        if item_name not in self.items or self.items[item_name][1] < quantity:
            raise ValueError(f"재고 부족: {item_name}")
        self.items[item_name] = (self.items[item_name][0], self.items[item_name][1] - quantity)

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = OrderStatus.PENDING
        self.update_total()

    def update_total(self) -> None:
        total_price = sum(item.price_per_unit * item.quantity for item in self.items)
        self.total = total_price * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        
        for item in items:
            inventory.reduce_stock(item.name, item.quantity)
        
        self.orders[order_id] = Order(order_id, items)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED
        else:
            raise ValueError("Invalid status to confirm an order")

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.SHIPPED
        else:
            raise ValueError("Invalid status to ship an order")

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        order = self.orders[order_id]
        if order.status == OrderStatus.PENDING or order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.CANCELLED
        elif order.status == OrderStatus.SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def process_payment(self, order_id: int, amount: float, method: str) -> Payment:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order does not exist")
        if amount != order.total:
            raise ValueError("Payment amount does not match order total")

        payment_id = max(self.payments.keys(), default=0) + 1
        payment = Payment(payment_id, order_id, amount, method)
        self.payments[payment_id] = payment

        order.status = OrderStatus.CONFIRMED
        return payment

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values()]

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 재고 관리 시스템 초기화
    inventory = Inventory()
    inventory.add_item("Apple", 0.5, 2)
    inventory.add_item("Banana", 0.3, 3)
    inventory.add_item("Bread", 2.0, 1)
    inventory.add_item("Milk", 1.5, 2)

    # 주문 추가
    items1 = [Item("Apple", 0.5, 2), Item("Banana", 0.3, 3)]
    manager.add_order(1, items1, inventory)
    
    items2 = [Item("Bread", 2.0, 1), Item("Milk", 1.5, 2)]
    manager.add_order(2, items2, inventory)
    
    # 결제 처리
    payment = manager.process_payment(1, order.total, method="Credit Card")
    print(f"Payment ID: {payment.payment_id}, Order ID: {payment.order_id}, Amount: {payment.amount}, Method: {payment.method}")
    
    # 주문 확인
    try:
        manager.confirm_order(1)
        print("Order confirmed")
    except ValueError as e:
        print(e)

    # 주문 배송
    try:
        manager.ship_order(1)
        print("Order shipped")
    except ValueError as e:
        print(e)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")
    
    # 모든 주문 목록 출력
    orders = manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}, Status: {order.status}")
    
    # 주문 취소
    try:
        manager.cancel_order(1)
        print("Order cancelled")
    except ValueError as e:
        print(e)

    # 이미 취소된 주문을 다시 취소하려고 시도
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)