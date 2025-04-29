from __future__ import annotations

from collections.abc import Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class IterativeFor(Statement):
    """The iterative for, i.e. using pairs() or ipairs()"""

    def __init__(
        self,
        token: Token,
        namelist: Sequence[Name],
        explist: Sequence[Expression],
        body: Block,
    ):
        super().__init__(token, "IterativeFor")
        self.namelist: list[Name] = list(namelist)
        self.explist: list[Expression] = list(explist)
        self.body: Block = body
