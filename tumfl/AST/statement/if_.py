from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Block, Expression
    from tumfl.Token import Token


class If(Statement):
    """An if statement, may contain a block or other if as false condition"""

    def __init__(
        self,
        token: Token,
        test: Expression,
        true: Block,
        false: Optional[Block | If],
    ):
        super().__init__(token, "If")
        self.test: Expression = test
        self.true: Block = true
        self.false: Optional[Block | If] = false
