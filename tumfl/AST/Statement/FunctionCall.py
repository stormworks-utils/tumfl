from __future__ import annotations

from typing import Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Statement import Statement


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
