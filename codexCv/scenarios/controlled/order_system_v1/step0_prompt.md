Implement an `OrderManager` in Python.

Requirements:

- Define an `OrderStatus` enum with `PENDING`, `CONFIRMED`, and `CANCELLED`.
- Define an `Item` dataclass with `name: str`, `price: float`, `quantity: int`.
- Define an `Order` dataclass with `order_id: int`, `customer: str`, `items: list[Item]`, `status: OrderStatus`, `discount_rate: float = 0.0`, `shipping_fee: float = 0.0`.
- Implement `OrderManager.create_order(customer, items)` that creates a pending order and returns the new order id.
- Implement `OrderManager.confirm_order(order_id)` and `OrderManager.cancel_order(order_id)`.
- Implement `OrderManager.get_total(order_id)` that returns `sum(item.price * item.quantity) - discount + shipping`.

Return complete Python code only.
