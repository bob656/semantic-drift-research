import ast


def check_extract_span_signature(code: str) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "extract_span":
            arg_names = [arg.arg for arg in node.args.args]
            return arg_names[:4] == ["text", "start", "end", "normalize_whitespace"] or arg_names[:3] == ["text", "start", "end"]
    return False
