from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Expression, Name
    from tumfl.Token import Token


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
