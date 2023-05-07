from __future__ import annotations

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class Repeat(Statement):
    """The repeat ... until loop"""

    def __init__(self, token: Token, condition: Expression, body: Block):
        super().__init__(token, "Repeat")
        self.condition: Expression = condition
        self.body: Block = body
