from __future__ import annotations

from tumfl.Token import Token, TokenType
from .ASTNode import ASTNode


class Variable(ASTNode):
    def __init__(self, token: Token, id: str) -> None:
        super().__init__(token, "Variable")
        self.id: str = id

    @staticmethod
    def from_token(token: Token) -> Variable:
        assert token.type == TokenType.NAME
        value = token.value
        assert isinstance(value, str)
        return Variable(token, value)
