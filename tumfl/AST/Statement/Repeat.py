from __future__ import annotations

from .Block import Block
from .Statement import Statement
from tumfl.AST.Expression import Expression
from tumfl.Token import Token, TokenType


class Repeat(Statement):
    """The repeat ... until loop"""

    def __init__(
        self, token: Token, comment: list[str], condition: Expression, body: Block
    ):
        super().__init__(token, "Repeat", comment)
        self.condition: Expression = condition
        self.body: Block = body
