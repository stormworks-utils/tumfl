from __future__ import annotations

from tumfl.token import Token

from .statement import Statement


class Break(Statement):
    """The break statement to exit loops"""

    def __init__(self, token: Token):
        super().__init__(token, "Break")
