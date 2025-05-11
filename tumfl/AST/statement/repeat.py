from __future__ import annotations

from typing import TYPE_CHECKING

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Block, Expression
    from tumfl.Token import Token


class Repeat(Statement):
    """The repeat ... until loop"""

    def __init__(self, token: Token, condition: Expression, body: Block):
        super().__init__(token, "Repeat")
        self.condition: Expression = condition
        self.body: Block = body
