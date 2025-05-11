from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Expression
    from tumfl.Token import Token


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
