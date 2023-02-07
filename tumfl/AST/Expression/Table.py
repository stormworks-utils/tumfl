from __future__ import annotations

from .Expression import Expression
from .TableField import TableField
from tumfl.Token import Token, TokenType


class Table(Expression):
    """A lua table constructor, like {[1]=2, 3; b=4}"""

    def __init__(self, token: Token, fields: list[TableField]):
        super().__init__(token, "Table")
        self.fields: list[TableField] = fields
