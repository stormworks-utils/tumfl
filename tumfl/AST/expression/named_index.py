from __future__ import annotations

from typing import TYPE_CHECKING

from .variable import Variable

if TYPE_CHECKING:
    from tumfl.AST import Expression, Name
    from tumfl.Token import Token


class NamedIndex(Variable):
    """A named index, like a.b, c.e, NOT a["b"]"""

    def __init__(self, token: Token, lhs: Expression, variable_name: Name):
        super().__init__(token, "NamedIndex")
        self.lhs: Expression = lhs
        self.variable_name: Name = variable_name
