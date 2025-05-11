from __future__ import annotations

from tumfl.Token import Token, TokenType

from .expression import Expression


class String(Expression):
    """A lua string, like "abc" or [[abc]]"""

    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token, "String")
        self.value: str = value

    @staticmethod
    def from_token(token: Token) -> String:
        assert token.type == TokenType.STRING
        value = token.value
        assert isinstance(value, str)
        return String(token, value)
