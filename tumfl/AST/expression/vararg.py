from __future__ import annotations

from tumfl.Token import Token, TokenType

from .expression import Expression


class Vararg(Expression):
    """The vararg expression (...)"""

    def __init__(self, token: Token) -> None:
        super().__init__(token, "Vararg")

    @staticmethod
    def from_token(token: Token) -> Vararg:
        assert token.type == TokenType.ELLIPSIS
        return Vararg(token)
