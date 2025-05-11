from __future__ import annotations

from typing import TYPE_CHECKING

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Block, Expression
    from tumfl.Token import Token


class While(Statement):
    """The while loop"""

    def __init__(self, token: Token, condition: Expression, body: Block):
        super().__init__(token, "While")
        self.condition: Expression = condition
        self.body: Block = body
