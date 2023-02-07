from __future__ import annotations

from .Expression import Expression

from tumfl.Token import TokenType, Token


class Boolean(Expression):
    """A boolean value (true or false)"""

    def __init__(self, token: Token, value: bool) -> None:
        super().__init__(token, "Boolean")
        self.value: bool = value

    @staticmethod
    def from_token(token: Token) -> Boolean:
        assert token.type in [TokenType.TRUE, TokenType.FALSE]
        return Boolean(token, token.type == TokenType.TRUE)
