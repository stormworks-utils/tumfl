from __future__ import annotations
from typing import Optional

from .Statement import Statement
from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token, TokenType


class AttributedName:
    def __init__(self, name: str, attribute: Optional[str] = None):
        self.name: str = name
        self.attribute: Optional[str] = attribute

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
