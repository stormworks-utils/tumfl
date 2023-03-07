from __future__ import annotations

from .Block import Block
from .Statement import Statement
from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token, TokenType


class While(Statement):
    """The while loop"""

    def __init__(
        self, token: Token, comment: list[str], condition: Expression, body: Block
    ):
        super().__init__(token, "While", comment)
        self.condition: Expression = condition
        self.body: Block = body
