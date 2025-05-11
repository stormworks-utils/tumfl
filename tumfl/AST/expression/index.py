from __future__ import annotations

from typing import TYPE_CHECKING

from .variable import Variable

if TYPE_CHECKING:
    from tumfl.AST import Expression
    from tumfl.Token import Token


class Index(Variable):
    """A index, like a[1], b[c] or d["abc"]"""

    def __init__(self, token: Token, lhs: Expression, variable_name: Expression):
        super().__init__(token, "Index")
        self.lhs: Expression = lhs
        self.variable_name: Expression = variable_name
