from typing import List, Optional

class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

    @property
    def total_price(self) -> float:
        return self.price * self.quantity

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.update_total()

    def update_total(self) -> None:
        total_price = sum(item.total_price for item in self.items)
        self.total = total_price * (1 - self.discount_percent)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError("Order already exists")
        self.orders[order_id] = Order(order_id, items, discount_percent)

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        del self.orders[order_id]

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError("Order does not exist")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].update_total()

    def get_order_total(self, order_id: int) -> Optional[float]:
        order = self.get_order(order_id)
        return order.total if order else None

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    items1 = [Item("Apple", 0.5, 2), Item("Banana", 0.3, 3)]
    manager.add_order(1, items1, discount_percent=0.1)
    
    items2 = [Item("Bread", 2.0, 1), Item("Milk", 1.5, 2)]
    manager.add_order(2, items2, discount_percent=0.2)
    
    # 주문 조회
    order = manager.get_order(1)
    if order:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}")
    
    # 모든 주문 목록 출력
    orders = manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Items: {[item.name for item in order.items]}, Total: {order.total}")
    
    # 주문 취소
    manager.cancel_order(1)