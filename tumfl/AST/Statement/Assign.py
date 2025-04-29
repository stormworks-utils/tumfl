from __future__ import annotations

from collections.abc import Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Statement import Statement


class Assign(Statement):
    """The assignment statement, like a,b = 1,nil"""

    def __init__(
        self,
        token: Token,
        targets: Sequence[Expression],
        expressions: Sequence[Expression],
    ):
        super().__init__(token, "Assign")
        self.targets: list[Expression] = list(targets)
        self.expressions: list[Expression] = list(expressions)
