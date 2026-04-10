import ast


def check_final_price_signature(code: str) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "final_price":
            arg_names = [arg.arg for arg in node.args.args]
            return arg_names[:3] == ["price", "discount_percent", "tax_percent"] or arg_names[:2] == ["price", "discount_percent"]
    return False
