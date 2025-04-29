from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from tumfl.AST.ASTNode import ASTNode
from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token

from .Statement import Statement


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

    def parent(
        self, parent: Optional[ASTNode], file_name: Optional[Path] = None
    ) -> None:
        # due to attributed names not being AST nodes, the auto implementation does not work
        self.parent_class = parent
        for name in self.variable_names:
            name.name.parent(self)
            if name.attribute:
                name.attribute.parent(self)

        if self.expressions:
            for expr in self.expressions:
                expr.parent(self)
