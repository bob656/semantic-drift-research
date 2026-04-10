def run_checks(candidate):
    results = []

    try:
        item = candidate.Item(name="apple", price=10.0, quantity=1)
        manager = candidate.OrderManager()
        order_id = manager.create_order("alice", [item])
        manager.confirm_order(order_id)
        reserve_result = manager.reserve_inventory(order_id)

        results.extend(
            [
                {"target": "reserve_inventory_exists", "status": "pass", "details": "method invoked successfully"},
                {"target": "reserve_inventory_callable", "status": "pass" if reserve_result is None or reserve_result is True or reserve_result is not False else "fail", "details": f"unexpected reserve result: {reserve_result}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step3_exception", "status": "fail", "details": str(exc)})

    return results
