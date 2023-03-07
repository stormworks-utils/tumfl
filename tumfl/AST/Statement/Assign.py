from __future__ import annotations

from .Statement import Statement
from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Variable import Variable
from tumfl.Token import Token, TokenType


class Assign(Statement):
    """The assignment statement, like a,b = 1,nil"""

    def __init__(
        self,
        token: Token,
        comment: list[str],
        targets: list[Variable],
        expressions: list[Expression],
    ):
        super().__init__(token, "Assign", comment)
        self.targets: list[Variable] = targets
        self.expressions: list[Expression] = expressions
