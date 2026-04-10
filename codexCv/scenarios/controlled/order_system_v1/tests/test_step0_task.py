def run_checks(candidate):
    results = []

    try:
        item1 = candidate.Item(name="apple", price=5.0, quantity=2)
        item2 = candidate.Item(name="milk", price=3.0, quantity=1)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item1, item2])
        order = manager.get_order(order_id)

        total = manager.get_total(order_id)
        manager.confirm_order(order_id)
        confirmed = manager.get_order(order_id)
        manager.cancel_order(order_id)
        cancelled = manager.get_order(order_id)

        results.extend(
            [
                {"target": "create_order", "status": "pass" if order is not None else "fail", "details": "order retrieval after creation"},
                {"target": "pending_status", "status": "pass" if getattr(order, "status", None) == candidate.OrderStatus.PENDING else "fail", "details": "new orders should start pending"},
                {"target": "initial_total", "status": "pass" if abs(total - 13.0) < 1e-6 else "fail", "details": f"expected 13.0, got {total}"},
                {"target": "confirm_order", "status": "pass" if getattr(confirmed, "status", None) == candidate.OrderStatus.CONFIRMED else "fail", "details": "confirm should update status"},
                {"target": "cancel_order", "status": "pass" if getattr(cancelled, "status", None) == candidate.OrderStatus.CANCELLED else "fail", "details": "cancel should mark order cancelled"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step0_exception", "status": "fail", "details": str(exc)})

    return results
