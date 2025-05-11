from __future__ import annotations

from tumfl.Token import Token, TokenType

from .variable import Variable


class Name(Variable):
    """The name of the variable, like a, b or very_long_variable_name, NOT a.b"""

    def __init__(self, token: Token, name: str):
        super().__init__(token, "Name")
        self.variable_name: str = name

    @staticmethod
    def from_token(token: Token) -> Name:
        assert token.type == TokenType.NAME
        assert isinstance(token.value, str)
        return Name(token, token.value)

    def __str__(self) -> str:
        return self.variable_name

    def clone(self) -> Name:
        return Name(self.token, self.variable_name)
