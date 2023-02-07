from __future__ import annotations

from .Expression import Expression
from .Variable import Variable
from tumfl.Token import Token, TokenType


class NamedIndex(Variable):
    """A named index, like a.b, c.e, NOT a["b"]"""

    def __init__(self, token: Token, lhs: Expression, name: str):
        super().__init__(token, "NamedIndex")
        self.lhs: Expression = lhs
        self.variable_name: str = name
