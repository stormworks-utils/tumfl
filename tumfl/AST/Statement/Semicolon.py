from __future__ import annotations

from tumfl.Token import Token

from .Statement import Statement


class Semicolon(Statement):
    """A semicolon"""

    def __init__(self, token: Token):
        super().__init__(token, "Semicolon")
