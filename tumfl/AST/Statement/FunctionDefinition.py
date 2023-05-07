from __future__ import annotations

from typing import Optional

from tumfl.AST.BaseFunctionDefinition import BaseFunctionDefinition
from tumfl.AST.Expression.Name import Name
from tumfl.AST.Expression.Vararg import Vararg
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class FunctionDefinition(Statement):
    """Definition of a lua function, NOT local"""

    def __init__(
        self,
        token: Token,
        names: list[Name],
        method_name: Optional[Name],
        parameters: list[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "FunctionDefinition")
        self.names: list[Name] = names
        self.method_name: Optional[Name] = method_name
        self.parameters: list[Name | Vararg] = parameters
        self.body: Block = body

    @staticmethod
    def from_base_definition(
        base: BaseFunctionDefinition,
        names: list[Name],
        method_name: Optional[Name],
    ) -> FunctionDefinition:
        return FunctionDefinition(
            base.token, names, method_name, base.parameters, base.body
        )
