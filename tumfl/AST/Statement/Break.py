from __future__ import annotations

from .Statement import Statement
from tumfl.Token import Token, TokenType


class Break(Statement):
    """The break statement to exit loops"""

    def __init__(self, token: Token):
        super().__init__(token, "Break")
