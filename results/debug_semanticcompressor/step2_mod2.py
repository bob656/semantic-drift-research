from typing import List, Optional, dataclass

@dataclass
class Item:
    name: str
    price: float
    quantity: int

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = self.calculate_total()

    def calculate_total(self) -> float:
        total = sum(item.price * item.quantity for item in self.items)
        return total - (total * self.discount_percent)

class OrderManager:
    def __init__(self):
        # 주문을 저장할 딕셔너리. 키는 order_id, 값은 Order 객체입니다.
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            print(f"Order ID {order_id} already exists.")
        else:
            new_order = Order(order_id, items, discount_percent)
            self.orders[order_id] = new_order
            print(f"Order added with ID: {order_id}")

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id in self.orders:
            del self.orders[order_id]
            print(f"Order with ID {order_id} cancelled.")
        else:
            print(f"No order found with ID {order_id}")

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if 0.0 <= discount_percent <= 1.0:
            order = self.get_order(order_id)
            if order:
                order.discount_percent = discount_percent
                order.total = order.calculate_total()
                print(f"Discount applied to Order ID {order_id}. New total: ${order.total}")
            else:
                print(f"No order found with ID {order_id}")
        else:
            print("Discount percent must be between 0.0 and 1.0.")

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        if order:
            return order.total
        else:
            print(f"No order found with ID {order_id}")
            return None

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    items1 = [Item("Apple", 2.99, 2), Item("Banana", 0.49, 5)]
    manager.add_order(1, items1)

    items2 = [Item("Cherry", 3.49, 1)]
    manager.add_order(2, items2)

    # 할인 적용
    manager.apply_discount(1, 0.1)  # Order 1에 10% 할인 적용

    # 주문 조회
    order_1 = manager.get_order(1)
    if order_1:
        print(f"Order 1: {order_1.items}, Total: ${order_1.total}")

    # 주문 취소
    manager.cancel_order(2)

    # 모든 주문 목록 출력
    all_orders = manager.list_orders()
    for order in all_orders:
        print(f"ID: {order.order_id}, Items: {order.items}, Total: ${order.total}")