from __future__ import annotations

from .Statement import Statement
from tumfl.Token import Token, TokenType


class Break(Statement):
    """The break statement to exit loops"""

    def __init__(self, token: Token, comment: list[str]):
        super().__init__(token, "Break", comment)

    @staticmethod
    def from_token(token: Token, comment: list[str]) -> Break:
        assert token.type == TokenType.BREAK
        return Break(token, comment)
