from __future__ import annotations

from .Statement import Statement
from tumfl.Token import Token, TokenType


class Label(Statement):
    """A label to be used with goto"""

    def __init__(self, token: Token, comment: list[str], label_name: str):
        super().__init__(token, "Label", comment)
        self.label_name: str = label_name
