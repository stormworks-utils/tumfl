from __future__ import annotations

from tumfl.Token import Token, TokenType

from .expression import Expression


class Nil(Expression):
    """The nil value"""

    def __init__(self, token: Token) -> None:
        super().__init__(token, "Nil")

    @staticmethod
    def from_token(token: Token) -> Nil:
        assert token.type == TokenType.NIL
        return Nil(token)
