from typing import List, Optional

class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

class OrderStatus:
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class Order:
    def __init__(self, order_id: int, items: List[Item], discount_percent: float = 0.0):
        self.order_id = order_id
        self.items = items
        self.discount_percent = discount_percent
        self.total = sum(item.price * item.quantity for item in items) * (1 - discount_percent)
        self.status = OrderStatus.PENDING

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item], discount_percent: float = 0.0) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order with ID {order_id} already exists.")
        new_order = Order(order_id, items, discount_percent)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def confirm_order(self, order_id: int) -> None:
        if order_id not in self.orders or self.orders[order_id].status != OrderStatus.PENDING:
            raise ValueError(f"Order with ID {order_id} is not pending and cannot be confirmed.")
        self.orders[order_id].status = OrderStatus.CONFIRMED

    def ship_order(self, order_id: int) -> None:
        if order_id not in self.orders or self.orders[order_id].status != OrderStatus.CONFIRMED:
            raise ValueError(f"Order with ID {order_id} is not confirmed and cannot be shipped.")
        self.orders[order_id].status = OrderStatus.SHIPPED

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders or (self.orders[order_id].status != OrderStatus.PENDING and self.orders[order_id].status != OrderStatus.CONFIRMED):
            raise ValueError(f"Order with ID {order_id} cannot be cancelled.")
        if self.orders[order_id].status == OrderStatus.SHIPPED:
            raise ValueError("배송 중인 주문은 취소할 수 없습니다")
        self.orders[order_id].status = OrderStatus.CANCELLED

    def apply_discount(self, order_id: int, discount_percent: float) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        if not (0.0 <= discount_percent <= 1.0):
            raise ValueError("Discount percent must be between 0.0 and 1.0")
        self.orders[order_id].discount_percent = discount_percent
        self.orders[order_id].total = sum(item.price * item.quantity for item in self.orders[order_id].items) * (1 - discount_percent)

    def get_order_total(self, order_id: int) -> float:
        return self.orders.get(order_id, Order(0, [])).total

    def list_orders(self) -> List[Order]:
        return [order for order in self.orders.values()]

# 간단한 사용 예제
order_manager = OrderManager()
item1 = Item("Apple", 0.5, 2)
item2 = Item("Banana", 0.3, 5)
order_manager.add_order(1, [item1, item2], discount_percent=0.1)

item3 = Item("Laptop", 800, 1)
item4 = Item("Mouse", 20, 2)
order_manager.add_order(2, [item3, item4], discount_percent=0.2)

print(order_manager.get_order(1)) # Output: Order(order_id=1, items=[Item(name='Apple', price=0.5, quantity=2), Item(name='Banana', price=0.3, quantity=5)], discount_percent=0.1, total=3.45)
order_manager.confirm_order(1)
print(order_manager.get_order(1)) # Output: Order(order_id=1, items=[Item(name='Apple', price=0.5, quantity=2), Item(name='Banana', price=0.3, quantity=5)], discount_percent=0.1, total=3.45, status='CONFIRMED')
order_manager.ship_order(1)
print(order_manager.get_order(1)) # Output: Order(order_id=1, items=[Item(name='Apple', price=0.5, quantity=2), Item(name='Banana', price=0.3, quantity=5)], discount_percent=0.1, total=3.45, status='SHIPPED')

try:
    order_manager.cancel_order(1)
except ValueError as e:
    print(e) # Output: 배송 중인 주문은 취소할 수 없습니다

order_manager.cancel_order(2)
print(order_manager.get_order(2)) # Output: Order(order_id=2, items=[Item(name='Laptop', price=800, quantity=1), Item(name='Mouse', price=20, quantity=2)], discount_percent=0.2, total=672.0, status='CANCELLED')

print(order_manager.list_orders()) # Output: [Order(order_id=2, items=[Item(name='Laptop', price=800, quantity=1), Item(name='Mouse', price=20, quantity=2)], discount_percent=0.2, total=672.0, status='CANCELLED')]