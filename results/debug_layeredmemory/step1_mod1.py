from typing import List, Optional

class Item:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

class Order:
    def __init__(self, order_id: int, items: List[Item]):
        self.order_id = order_id
        self.items = items
        self.total = sum(item.price * item.quantity for item in items)

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id: int, items: List[Item]) -> None:
        if order_id in self.orders:
            raise ValueError(f"Order with ID {order_id} already exists.")
        new_order = Order(order_id, items)
        self.orders[order_id] = new_order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        del self.orders[order_id]

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())

# 간단한 사용 예제
order_manager = OrderManager()
item1 = Item("Apple", 0.5, 2)
item2 = Item("Banana", 0.3, 5)
order_manager.add_order(1, [item1, item2])

item3 = Item("Laptop", 800, 1)
item4 = Item("Mouse", 20, 2)
order_manager.add_order(2, [item3, item4])

print(order_manager.get_order(1)) # Output: Order(order_id=1, items=[Item(name='Apple', price=0.5, quantity=2), Item(name='Banana', price=0.3, quantity=5)], total=3.5)
print(order_manager.list_orders()) # Output: [Order(order_id=1, items=[Item(name='Apple', price=0.5, quantity=2), Item(name='Banana', price=0.3, quantity=5)], total=3.5), Order(order_id=2, items=[Item(name='Laptop', price=800, quantity=1), Item(name='Mouse', price=20, quantity=2)], total=840)]
order_manager.cancel_order(1)
print(order_manager.get_order(1)) # Output: None