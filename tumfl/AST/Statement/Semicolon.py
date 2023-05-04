from __future__ import annotations

from .Statement import Statement
from tumfl.Token import Token, TokenType


class Semicolon(Statement):
    """A semicolon"""

    def __init__(self, token: Token):
        super().__init__(token, "Semicolon")
