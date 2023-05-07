from __future__ import annotations

from tumfl.AST.BaseFunctionDefinition import BaseFunctionDefinition
from tumfl.AST.Statement.Block import Block
from tumfl.Token import Token

from .Expression import Expression
from .Name import Name
from .Vararg import Vararg


class ExpFunctionDefinition(Expression):
    """Definition of a lua function expression"""

    def __init__(
        self,
        token: Token,
        parameters: list[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "ExpFunctionDefinition")
        self.parameters: list[Name | Vararg] = parameters
        self.body: Block = body

    @staticmethod
    def from_base_definition(base: BaseFunctionDefinition) -> ExpFunctionDefinition:
        return ExpFunctionDefinition(base.token, base.parameters, base.body)
