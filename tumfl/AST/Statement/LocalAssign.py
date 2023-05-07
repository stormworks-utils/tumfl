from __future__ import annotations

from typing import Optional

from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token, TokenType

from .Statement import Statement


class AttributedName:
    def __init__(self, name: Name, attribute: Optional[Name] = None):
        self.name: Name = name
        self.attribute: Optional[Name] = attribute

    def __repr__(self) -> str:
        return f"AttributedName(name={self.name!r}, attribute={self.attribute!r})"


class LocalAssign(Statement):
    """Assignment of local variables"""

    def __init__(
        self,
        token: Token,
        variable_names: list[AttributedName],
        expressions: Optional[list[Expression]],
    ):
        super().__init__(token, "LocalAssign")
        self.variable_names: list[AttributedName] = variable_names
        self.expressions: Optional[list[Expression]] = expressions
