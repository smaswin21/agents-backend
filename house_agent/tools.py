# house_agent/tools.py
from typing import Dict, Optional

# very simple tool to see whether tool calling works :)


def add_numbers(a: float, b: float) -> str:
    """
    Return the sum of a and b as a string.
    Keep output a string (ToolMessage requires string content).
    """
    result = float(a) + float(b)
    print(f"TOOL CALLED: add_numbers({a}, {b}) -> {result}")
    return str(result)
