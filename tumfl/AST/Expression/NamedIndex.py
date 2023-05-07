from __future__ import annotations

from tumfl.Token import Token, TokenType

from .Expression import Expression
from .Name import Name
from .Variable import Variable


class NamedIndex(Variable):
    """A named index, like a.b, c.e, NOT a["b"]"""

    def __init__(self, token: Token, lhs: Expression, name: Name):
        super().__init__(token, "NamedIndex")
        self.lhs: Expression = lhs
        self.variable_name: Name = name
