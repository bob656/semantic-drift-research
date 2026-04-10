Add shipping support without breaking the existing interface.

Requirements:

- Add `set_shipping_fee(order_id, fee)`.
- `create_order(customer, items)` must stay callable as-is.
- `get_total(order_id)` must now include the latest shipping fee.

Return complete Python code only.
