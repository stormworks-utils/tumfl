from __future__ import annotations

from abc import ABC

from tumfl.AST.ASTNode import ASTNode
from tumfl.Token import Token

from .Expression import Expression
from .Name import Name


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
