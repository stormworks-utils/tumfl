from __future__ import annotations

from .Statement import Statement
from .Block import Block
from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token, TokenType


class IterativeFor(Statement):
    """The iterative for, i.e. using pairs() or ipairs()"""

    def __init__(
        self,
        token: Token,
        namelist: list[Name],
        explist: list[Expression],
        body: Block,
    ):
        super().__init__(token, "IterativeFor")
        self.namelist: list[Name] = namelist
        self.explist: list[Expression] = explist
        self.body: Block = body
