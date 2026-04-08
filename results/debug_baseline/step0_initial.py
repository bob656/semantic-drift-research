class Order:
    def __init__(self, order_id, items, total):
        self.order_id = order_id
        self.items = items
        self.total = total

class OrderManager:
    def __init__(self):
        self.orders = {}

    def add_order(self, order_id, items, total):
        if order_id not in self.orders:
            new_order = Order(order_id, items, total)
            self.orders[order_id] = new_order
            return True
        return False

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False

    def list_orders(self):
        return list(self.orders.values())

# 간단한 사용 예제
if __name__ == "__main__":
    manager = OrderManager()
    
    # 주문 추가
    manager.add_order(1, ["Apple", "Banana"], 2.5)
    manager.add_order(2, ["Coffee", "Tea"], 3.0)
    
    # 주문 조회
    order = manager.get_order(1)
    print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")
    
    # 주문 취소
    manager.cancel_order(2)
    
    # 모든 주문 목록
    orders = manager.list_orders()
    for order in orders:
        print(f"Order ID: {order.order_id}, Items: {order.items}, Total: {order.total}")