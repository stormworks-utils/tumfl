from __future__ import annotations

from .Statement import Statement
from tumfl.Token import Token, TokenType


class Goto(Statement):
    """The goto statement"""

    def __init__(self, token: Token, comment: list[str], label_name: str):
        super().__init__(token, "Goto", comment)
        self.label_name: str = label_name
