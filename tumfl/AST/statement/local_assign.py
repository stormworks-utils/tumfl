from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Expression, Name
    from tumfl.Token import Token


class AttributedName:
    def __init__(self, name: Name, attribute: Optional[Name] = None):
        self.name: Name = name
        self.attribute: Optional[Name] = attribute

    def __repr__(self) -> str:
        return f"AttributedName(name={self.name!r}, attribute={self.attribute!r})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, AttributedName):
            return self.name == other.name and self.attribute == other.attribute
        return False

    def __str__(self) -> str:
        if self.attribute:
            return f"{self.name.variable_name} <{self.attribute.variable_name}>"
        return self.name.variable_name


class LocalAssign(Statement):
    """Assignment of local variables"""

    def __init__(
        self,
        token: Token,
        variable_names: Sequence[AttributedName],
        expressions: Optional[Sequence[Expression]],
    ):
        super().__init__(token, "LocalAssign")
        self.variable_names: list[AttributedName] = list(variable_names)
        self.expressions: Optional[list[Expression]] = (
            list(expressions) if expressions is not None else None
        )
