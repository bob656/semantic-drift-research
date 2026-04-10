Add percentage discount support.

Requirements:

- Add `apply_discount(order_id, discount_rate)`.
- `discount_rate` is between `0.0` and `1.0`.
- `get_total(order_id)` should remain consistent with existing shipping behavior.
- Cancellation semantics must remain unchanged.

Return complete Python code only.
