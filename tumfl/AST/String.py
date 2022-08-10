from __future__ import annotations

from .ASTNode import ASTNode
from tumfl.Token import Token, TokenType


class String(ASTNode):
    def __init__(self, token: Token, value: str) -> None:
        super().__init__(token, "String")
        self.value: str = value

    @staticmethod
    def from_token(token: Token) -> String:
        assert token.type == TokenType.STRING
        value = token.value
        assert isinstance(value, str)
        return String(token, value)
