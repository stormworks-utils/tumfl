from __future__ import annotations

from typing import TYPE_CHECKING

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Name
    from tumfl.Token import Token


class Goto(Statement):
    """The goto statement"""

    def __init__(self, token: Token, label_name: Name):
        super().__init__(token, "Goto")
        self.label_name: Name = label_name
