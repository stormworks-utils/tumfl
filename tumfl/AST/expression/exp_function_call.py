from __future__ import annotations

from typing import Sequence

from tumfl.Token import Token

from .expression import Expression


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
