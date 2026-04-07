from typing import List, Optional
from dataclasses import dataclass
import datetime

# Item 클래스 추가 및 stock 필드 추가
@dataclass
class Item:
    name: str
    price: float
    quantity: int
    stock: int  # 현재 재고 수량

# Payment 클래스 추가
@dataclass
class Payment:
    payment_id: int
    order_id: int
    amount: float
    method: str

# Inventory 클래스 추가
class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name: str, price: float, stock: int) -> None:
        if item_name in self.items:
            print(f"Item '{item_name}' already exists.")
        else:
            self.items[item_name] = Item(name=item_name, price=price, quantity=0, stock=stock)
            print(f"Item '{item_name}' added to inventory.")

    def get_stock(self, item_name: str) -> Optional[int]:
        item = self.items.get(item_name)
        if item:
            return item.stock
        else:
            print(f"Item '{item_name}' not found.")
            return None

    def reduce_stock(self, item_name: str, quantity: int) -> None:
        item = self.items.get(item_name)
        if item and item.stock >= quantity:
            item.stock -= quantity
            print(f"Reduced stock for '{item_name}' by {quantity}. Remaining stock: {item.stock}")
        else:
            raise ValueError(f"재고 부족: {item_name}")

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.status = "PENDING"  # 주문 상태 추가
        self.created_at = datetime.datetime.now()  # 주문 생성 시각 추가
        # Order.total은 items의 price * quantity 합계에서 할인을 적용한 최종 금액으로 계산
        self.update_total()

    def update_total(self) -> None:
        subtotal = sum(item.price * item.quantity for item in self.items)
        self.total = subtotal - (subtotal * self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리, key는 order_id, value는 Order 객체
        self.orders = {}
        # 결제 정보를 저장할 딕셔너리, key는 payment_id, value는 Payment 객체
        self.payments = {}

    def add_order(self, order_id: int, items: List[Item], inventory: Inventory) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            try:
                # 재고 차감 시도
                for item in items:
                    inventory.reduce_stock(item.name, item.quantity)
                # 주문 생성 및 저장
                self.orders[order_id] = Order(order_id, items, discount_percent=0.0)
                print(f"Order ID {order_id} added.")
            except ValueError as e:
                print(e)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print(f"Order ID {order_id} cannot be confirmed.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print(f"Order ID {order_id} cannot be shipped.")

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and (order.status == "PENDING" or order.status == "CONFIRMED"):
            order.status = "CANCELLED"
            print(f"Order ID {order_id} canceled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print(f"Order ID {order_id} not found.")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        order = self.get_order(order_id)
        if order:
            if 0.0 <= discount_percent <= 1.0:
                order.discount_percent = discount_percent
                order.update_total()
                print(f"Order ID {order_id} updated with discount {discount_percent * 100}%.")
            else:
                print("Invalid discount percent. It should be between 0.0 and 1.0.")
        else:
            print(f"Order ID {order_id} not found.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"Order ID {order_id} not found.")
            return None

    def process_payment(self, order_id: int, amount: float, method: str) -> Optional[Payment]:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            if amount == order.total:
                payment_id = len(self.payments) + 1
                payment = Payment(payment_id=payment_id, order_id=order_id, amount=amount, method=method)
                self.payments[payment_id] = payment
                order.status = "CONFIRMED"
                print(f"Order ID {order_id} processed with {method}.")
                return payment
            else:
                raise ValueError("Amount does not match the total order amount.")
        else:
            print(f"Order ID {order_id} cannot be processed for payment.")
            return None

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_orders(self) -> List[Order]:
        # 활성 주문만 반환
        return [order for order in self.orders.values() if order.status != "CANCELLED"]

    def get_order_history(self) -> List[Order]:
        # 모든 주문을 생성 시각(created_at) 기준으로 정렬하여 반환
        return sorted(self.orders.values(), key=lambda o: o.created_at)

    def get_orders_by_status(self, status: str) -> List[Order]:
        # 지정한 상태의 주문만 반환
        return [order for order in self.orders.values() if order.status == status]

# 간단한 사용 예제
if __name__ == "__main__":
    order_manager = OrderManager()
    inventory = Inventory()

    # 재고 등록
    inventory.add_item("item1", 5.25, 3)
    inventory.add_item("item2", 3.00, 5)
    inventory.add_item("item3", 7.50, 4)

    # 주문 추가
    item1 = Item(name="item1", price=5.25, quantity=2, stock=0)
    item2 = Item(name="item2", price=3.00, quantity=1, stock=0)
    order_manager.add_order(1, [item1, item2], inventory)

    # 주문 이력 조회
    history = order_manager.get_order_history()
    print("Order History:")
    for order in history:
        print(f"Order ID {order.order_id}, Status: {order.status}, Created At: {order.created_at}")

    # 특정 상태의 주문 조회
    pending_orders = order_manager.get_orders_by_status("PENDING")
    print("\nPending Orders:")
    for order in pending_orders:
        print(f"Order ID {order.order_id}, Status: {order.status}")

    # 취소 시도
    try:
        order_manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 취소된 주문을 포함한 이력 조회
    history = order_manager.get_order_history()
    print("\nOrder History After Cancellation:")
    for order in history:
        print(f"Order ID {order.order_id}, Status: {order.status}, Created At: {order.created_at}")