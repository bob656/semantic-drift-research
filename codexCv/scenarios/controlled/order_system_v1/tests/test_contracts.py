def run_checks(candidate):
    results = []

    try:
        item = candidate.Item(name="apple", price=10.0, quantity=2)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item])
        manager.cancel_order(order_id)
        order = manager.get_order(order_id)

        reconfirmed = False
        try:
            manager.confirm_order(order_id)
            order = manager.get_order(order_id)
            reconfirmed = getattr(order, "status", None) == candidate.OrderStatus.CONFIRMED
        except Exception:
            reconfirmed = False

        results.append(
            {
                "target": "test_cancel_is_terminal",
                "status": "pass" if getattr(order, "status", None) == candidate.OrderStatus.CANCELLED and not reconfirmed else "fail",
                "details": "cancelled orders should not transition back to confirmed",
            }
        )
    except Exception as exc:
        results.append({"target": "test_cancel_is_terminal", "status": "fail", "details": str(exc)})

    try:
        item = candidate.Item(name="apple", price=10.0, quantity=2)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item])
        manager.set_shipping_fee(order_id, 5.0)
        manager.apply_discount(order_id, 0.1)
        total = manager.get_total(order_id)
        expected = 23.0
        results.append(
            {
                "target": "test_total_consistency",
                "status": "pass" if abs(total - expected) < 1e-6 else "fail",
                "details": f"expected {expected}, got {total}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_total_consistency", "status": "fail", "details": str(exc)})

    return results
