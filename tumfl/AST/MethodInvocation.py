from __future__ import annotations
from typing import Optional

from tumfl.AST.Expression import Expression
from tumfl.AST.Statement import Statement
from tumfl.Token import Token, TokenType


class MethodInvocation(Expression, Statement):
    """A method invocation, may be a statement or an expression. Like f:b(a,b,c) or f:b()"""

    def __init__(
        self,
        token: Token,
        variable: Expression,
        method: str,
        arguments: list[Expression],
        comment: Optional[list[str]] = None,
    ):
        super().__init__(token, "MethodInvocation", comment=comment or [])
        self.function: Expression = variable
        self.method: str = method
        self.arguments: list[Expression] = arguments
