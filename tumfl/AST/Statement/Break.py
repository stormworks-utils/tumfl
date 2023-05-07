from __future__ import annotations

from tumfl.Token import Token

from .Statement import Statement


class Break(Statement):
    """The break statement to exit loops"""

    def __init__(self, token: Token):
        super().__init__(token, "Break")
