from __future__ import annotations
from typing import Optional

from .Statement import Statement
from .Block import Block
from tumfl.AST.Expression import Expression
from tumfl.Token import Token, TokenType


class NumericFor(Statement):
    """The numeric for, i.e. for i=1,10 do"""

    def __init__(
        self,
        token: Token,
        comment: list[str],
        name: str,
        start: Expression,
        stop: Expression,
        step: Optional[Expression],
        body: Block,
    ):
        super().__init__(token, "NumericFor", comment)
        self.name: str = name
        self.start: Expression = start
        self.stop: Expression = stop
        self.step: Optional[Expression] = step
        self.body: Block = body
