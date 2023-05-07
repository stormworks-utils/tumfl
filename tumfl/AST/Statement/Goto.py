from __future__ import annotations

from tumfl.AST.Expression.Name import Name
from tumfl.Token import Token

from .Statement import Statement


class Goto(Statement):
    """The goto statement"""

    def __init__(self, token: Token, label_name: Name):
        super().__init__(token, "Goto")
        self.label_name: Name = label_name
