from __future__ import annotations

from collections.abc import Sequence

from tumfl.Token import Token

from .Expression import Expression


class ExpFunctionCall(Expression):
    """A function call, may be a statement or an expression. Like f(a,b,c) or f()"""

    def __init__(
        self,
        token: Token,
        function: Expression,
        arguments: Sequence[Expression],
    ):
        super().__init__(token, "ExpFunctionCall")
        self.function: Expression = function
        self.arguments: list[Expression] = list(arguments)
