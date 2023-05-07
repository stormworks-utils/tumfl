from __future__ import annotations

from tumfl.AST.BaseFunctionDefinition import BaseFunctionDefinition
from tumfl.AST.Expression.Name import Name
from tumfl.AST.Expression.Vararg import Vararg
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class LocalFunctionDefinition(Statement):
    """Definition for a local function"""

    def __init__(
        self,
        token: Token,
        function_name: Name,
        parameters: list[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "LocalFunctionDefinition")
        self.function_name: Name = function_name
        self.parameters: list[Name | Vararg] = parameters
        self.body: Block = body

    @staticmethod
    def from_base_definition(
        base: BaseFunctionDefinition, function_name: Name
    ) -> LocalFunctionDefinition:
        return LocalFunctionDefinition(
            base.token, function_name, base.parameters, base.body
        )
