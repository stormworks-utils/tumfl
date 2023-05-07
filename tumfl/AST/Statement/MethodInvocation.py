from __future__ import annotations

from typing import Optional

from tumfl.AST.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token, TokenType

from .Statement import Statement


class MethodInvocation(Statement):
    """A method invocation, may be a statement or an expression. Like f:b(a,b,c) or f:b()"""

    def __init__(
        self,
        token: Token,
        variable: Expression,
        method: Name,
        arguments: list[Expression],
    ):
        super().__init__(token, "MethodInvocation")
        self.function: Expression = variable
        self.method: Name = method
        self.arguments: list[Expression] = arguments
