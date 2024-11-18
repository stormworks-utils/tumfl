from __future__ import annotations

from typing import Optional

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Statement import Statement


class Block(Statement):
    """A block consisting of statements"""

    def __init__(
        self,
        token: Token,
        statements: list[Statement],
        returns: Optional[list[Expression]],
    ):
        super().__init__(token, "Block")
        self.statements: list[Statement] = statements
        self.returns: Optional[list[Expression]] = returns
