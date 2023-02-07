from __future__ import annotations
from typing import Optional

from tumfl.AST.Expression import Expression
from tumfl.AST.Statement import Statement
from tumfl.Token import Token, TokenType


class FunctionCall(Expression, Statement):
    """A function call, may be a statement or an expression. Like f(a,b,c) or f()"""

    def __init__(
        self,
        token: Token,
        function: Expression,
        arguments: list[Expression],
        comment: Optional[list[str]],
    ):
        super().__init__(token, "FunctionCall", comment=comment or [])
        self.function: Expression = function
        self.arguments: list[Expression] = arguments
