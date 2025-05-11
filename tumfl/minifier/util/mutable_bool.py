from __future__ import annotations


class MutableBool:
    """This is simply a class that can be shared, and has a bool with interior mutability"""

    def __init__(self, value: bool):
        self.value = value

    def __bool__(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return f"MutableBool({self.value})"

    def __or__(self, other: bool | MutableBool) -> bool:
        self.value = self.value or bool(other)
        return self.value
