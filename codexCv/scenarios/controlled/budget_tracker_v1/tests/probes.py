import ast


def check_add_expense_signature(code: str) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "add_expense":
            arg_names = [arg.arg for arg in node.args.args]
            return arg_names[:3] == ["self", "category", "amount"]
    return False
