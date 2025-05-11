from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Expression
    from tumfl.Token import Token


class FunctionCall(Statement):
    """A function call, may be a statement or an expression. Like f(a,b,c) or f()"""

    def __init__(
        self,
        token: Token,
        function: Expression,
        arguments: Sequence[Expression],
    ):
        super().__init__(token, "FunctionCall")
        self.function: Expression = function
        self.arguments: list[Expression] = list(arguments)
