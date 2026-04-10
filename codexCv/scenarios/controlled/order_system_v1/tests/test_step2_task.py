def run_checks(candidate):
    results = []

    try:
        item = candidate.Item(name="apple", price=20.0, quantity=1)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item])
        manager.set_shipping_fee(order_id, 5.0)
        manager.apply_discount(order_id, 0.25)
        total = manager.get_total(order_id)

        results.extend(
            [
                {"target": "apply_discount_exists", "status": "pass", "details": "method invoked successfully"},
                {"target": "discount_applied", "status": "pass" if abs(total - 20.0) < 1e-6 else "fail", "details": f"expected 20.0, got {total}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step2_exception", "status": "fail", "details": str(exc)})

    return results
