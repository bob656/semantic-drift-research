def run_checks(candidate):
    results = []

    try:
        item = candidate.Item(name="apple", price=10.0, quantity=1)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item])
        manager.set_shipping_fee(order_id, 4.5)
        total = manager.get_total(order_id)

        results.extend(
            [
                {"target": "set_shipping_fee_exists", "status": "pass", "details": "method invoked successfully"},
                {"target": "shipping_applied", "status": "pass" if abs(total - 14.5) < 1e-6 else "fail", "details": f"expected 14.5, got {total}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step1_exception", "status": "fail", "details": str(exc)})

    return results
