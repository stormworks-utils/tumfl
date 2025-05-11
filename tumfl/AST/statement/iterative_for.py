from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Block, Expression, Name
    from tumfl.Token import Token


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
