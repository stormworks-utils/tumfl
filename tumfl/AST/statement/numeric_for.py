from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Block, Expression, Name
    from tumfl.Token import Token


class NumericFor(Statement):
    """The numeric for, i.e. for i=1,10 do"""

    def __init__(
        self,
        token: Token,
        variable_name: Name,
        start: Expression,
        stop: Expression,
        step: Optional[Expression],
        body: Block,
    ):
        super().__init__(token, "NumericFor")
        self.variable_name: Name = variable_name
        self.start: Expression = start
        self.stop: Expression = stop
        self.step: Optional[Expression] = step
        self.body: Block = body
