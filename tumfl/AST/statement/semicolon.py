from __future__ import annotations

from tumfl.token import Token

from .statement import Statement


class Semicolon(Statement):
    """A semicolon"""

    def __init__(self, token: Token):
        super().__init__(token, "Semicolon")
