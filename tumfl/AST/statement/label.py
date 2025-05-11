from __future__ import annotations

from typing import TYPE_CHECKING

from tumfl.Token import Token

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Name


class Label(Statement):
    """A label to be used with goto"""

    def __init__(self, token: Token, label_name: Name):
        super().__init__(token, "Label")
        self.label_name: Name = label_name
