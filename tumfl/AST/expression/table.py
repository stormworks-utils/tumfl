from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from tumfl.Token import Token

from .expression import Expression

if TYPE_CHECKING:
    from tumfl.AST import TableField


class Table(Expression):
    """A lua table constructor, like {[1]=2, 3; b=4}"""

    def __init__(self, token: Token, fields: Sequence[TableField]):
        super().__init__(token, "Table")
        self.fields: list[TableField] = list(fields)
