import ast

def evaluate_string_as_list(string_value: str):
    try:
        return ast.literal_eval(string_value)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Failed to parse list from string: {e}")