from __future__ import annotations

from typing import Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token

from .Statement import Statement


class MethodInvocation(Statement):
    """A method invocation, may be a statement or an expression. Like f:b(a,b,c) or f:b()"""

    def __init__(
        self,
        token: Token,
        function: Expression,
        method: Name,
        arguments: Sequence[Expression],
    ):
        super().__init__(token, "MethodInvocation")
        self.function: Expression = function
        self.method: Name = method
        self.arguments: list[Expression] = list(arguments)
