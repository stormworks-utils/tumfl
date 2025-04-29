from __future__ import annotations

from collections.abc import Sequence

from tumfl.Token import Token

from .Expression import Expression
from .Name import Name


class ExpMethodInvocation(Expression):
    """A method invocation, may be a statement or an expression. Like f:b(a,b,c) or f:b()"""

    def __init__(
        self,
        token: Token,
        function: Expression,
        method: Name,
        arguments: Sequence[Expression],
    ):
        super().__init__(token, "ExpMethodInvocation")
        self.function: Expression = function
        self.method: Name = method
        self.arguments: list[Expression] = list(arguments)
