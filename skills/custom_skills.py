import os
from langchain_core.tools import tool

@tool
def calculate_math_expression(expression: str) -> str:

    #Pass a mathematical expression here as a string (for example: '2500 * 1.15').

    try:
        allowed_chars = "0123456789+-*/(). "
        if not all(c in allowed_chars for c in expression):
            return "Security error: invalid characters detected."
        result = eval(expression, {"__builtins__": None}, {})
        return f"Calculation result: {result}"
    except Exception as e:
        return f"Error during calculation: {str(e)}"