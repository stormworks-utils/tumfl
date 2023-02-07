from __future__ import annotations

from .Statement import Statement
from tumfl.AST.Expression import Expression
from tumfl.Token import Token, TokenType


class Block(Statement):
    """A block consisting of statements"""

    def __init__(
        self,
        token: Token,
        comment: list[str],
        statements: list[Statement],
        returns: list[Expression],
    ):
        super().__init__(token, "Block", comment)
        self.statements: list[Statement] = statements
        self.returns: list[Expression] = returns
