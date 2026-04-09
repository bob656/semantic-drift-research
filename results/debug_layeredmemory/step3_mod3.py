from typing import List, Optional

class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = "PENDING"

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order ID already exists")
        new_order = Order(order_id, items, discount_percent)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status in ["PENDING", "CONFIRMED"]:
            order.status = "CANCELLED"
        else:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        order.discount_percent = discount_percent
        order.total = sum(item.price * item.quantity for item in order.items) * (1 - discount_percent)

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        return order.total

    def confirm_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status == "PENDING":
            order.status = "CONFIRMED"
        else:
            raise ValueError("주문 상태가 PENDING이 아닙니다")

    def ship_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("Order ID does not exist")
        
        if order.status == "CONFIRMED":
            order.status = "SHIPPED"
        else:
            raise ValueError("주문 상태가 CONFIRMED가 아닙니다")

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    items1 = [Item("apple", 0.99, 2), Item("banana", 0.59, 3)]
    items2 = [Item("orange", 0.79, 1)]
    manager.add_order(1, items1)
    manager.add_order(2, items2)

    # 주문 조회
    order_1 = manager.get_order(1)
    print(f"Order 1: {order_1.items[0].name} x {order_1.items[0].quantity}, "
          f"{order_1.items[1].name} x {order_1.items[1].quantity} - Total: ${order_1.total} - Status: {order_1.status}")

    # 주문 확인
    manager.confirm_order(1)
    
    # 확인된 후 주문 조회
    order_1 = manager.get_order(1)
    print(f"Order 1 after confirmation: {order_1.items[0].name} x {order_1.items[0].quantity}, "
          f"{order_1.items[1].name} x {order_1.items[1].quantity} - Total: ${order_1.total} - Status: {order_1.status}")

    # 주문 배송
    manager.ship_order(1)
    
    # 배송된 후 주문 조회
    order_1 = manager.get_order(1)
    print(f"Order 1 after shipping: {order_1.items[0].name} x {order_1.items[0].quantity}, "
          f"{order_1.items[1].name} x {order_1.items[1].quantity} - Total: ${order_1.total} - Status: {order_1.status}")

    # 주문 취소 시도 (배송 중인 주문은 취소할 수 없음)
    try:
        manager.cancel_order(1)
    except ValueError as e:
        print(e)

    # 취소된 후 주문 조회
    order_1 = manager.get_order(1)
    if order_1 is None:
        print("Order 1 has been cancelled.")
    else:
        print(f"Order 1 status after attempted cancellation: {order_1.status}")

    # 모든 주문 목록 출력
    for order in manager.list_orders():
        print(f"Order ID: {order.order_id}, Items: {[f'{item.name} x {item.quantity}' for item in order.items]}, "
              f"Total: ${order.total} - Status: {order.status}")