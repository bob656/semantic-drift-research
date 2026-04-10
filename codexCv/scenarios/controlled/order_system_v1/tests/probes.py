import ast


def check_create_order_signature(code: str) -> bool:
    """Return True when create_order(customer, items) is preserved."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "create_order":
            arg_names = [arg.arg for arg in node.args.args]
            return arg_names[:3] == ["self", "customer", "items"]
    return False
