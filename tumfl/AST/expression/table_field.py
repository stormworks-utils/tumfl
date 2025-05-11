from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from tumfl.AST.ast_node import ASTNode

if TYPE_CHECKING:
    from tumfl.AST import Expression, Name
    from tumfl.Token import Token


class TableField(ASTNode, ABC):
    """Base class for all table fields"""


class ExplicitTableField(TableField):
    """Table field of the form `[ expr ] = expr`"""

    def __init__(self, token: Token, at: Expression, value: Expression):
        super().__init__(token, "ExplicitTableField")
        self.at: Expression = at
        self.value: Expression = value


class NamedTableField(TableField):
    """Table field of the form `Name = expr`"""

    def __init__(self, token: Token, field_name: Name, value: Expression):
        super().__init__(token, "NamedTableField")
        self.field_name: Name = field_name
        self.value: Expression = value


class NumberedTableField(TableField):
    """Table field of the form `expr`"""

    def __init__(self, token: Token, value: Expression):
        super().__init__(token, "NumberedTableField")
        self.value: Expression = value
