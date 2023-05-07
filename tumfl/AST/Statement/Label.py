from __future__ import annotations

from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token

from .Statement import Statement


class Label(Statement):
    """A label to be used with goto"""

    def __init__(self, token: Token, label_name: Name):
        super().__init__(token, "Label")
        self.label_name: Name = label_name
