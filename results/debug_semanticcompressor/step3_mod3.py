from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

@dataclass
class Order:
    order_id: int
    items: List[Item]
    total: float
    discount_percent: float = 0.0
    status: str = "PENDING"

    def __post_init__(self):
        self.total = sum(item.price * item.quantity for item in self.items) * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], total: float) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            self.orders[order_id] = Order(order_id, items)
            print(f"Order with ID {order_id} added.")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "PENDING":
            order.status = "CONFIRMED"
            print(f"Order ID {order_id} confirmed.")
        else:
            print("Invalid status change.")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status == "CONFIRMED":
            order.status = "SHIPPED"
            print(f"Order ID {order_id} shipped.")
        else:
            print("Invalid status change.")

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order and order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
            print(f"Order ID {order_id} cancelled.")
        elif order and order.status == "SHIPPED":
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        else:
            print("Invalid status change.")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)
                print(f"Discount applied to Order ID {order_id}: {discount_percent*100}%")
            else:
                print(f"No order found with ID {order_id}")
        else:
            print("Invalid discount percent. Must be between 0.0 and 1.0.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}")
            return None

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    item1 = Item(name="item1", price=25.0, quantity=2)
    item2 = Item(name="item2", price=25.0, quantity=1)
    manager.add_order(1, [item1, item2], 75.0)

    item3 = Item(name="item3", price=30.0, quantity=1)
    manager.add_order(2, [item3], 30.0)

    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 주문 확정
    manager.confirm_order(1)

    # 주문 배송
    manager.ship_order(1)

    # 주문 취소 시도 (SHIPPED 상태)
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 주문 취소
    manager.cancel_order(2)

    # 모든 주문 목록
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")

    # 할인 적용 후 전체 주문 목록
    print("\nList of orders after applying discount:")
    manager.apply_discount(1, 0.1)
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Status: {order.status}, Items: {[f'{item.name} x{item.quantity}' for item in order.items]}, Total: {order.total}")