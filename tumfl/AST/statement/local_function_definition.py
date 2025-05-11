from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import BaseFunctionDefinition, Block, Name, Vararg
    from tumfl.Token import Token


class LocalFunctionDefinition(Statement):
    """Definition for a local function"""

    def __init__(
        self,
        token: Token,
        function_name: Name,
        parameters: Sequence[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "LocalFunctionDefinition")
        self.function_name: Name = function_name
        self.parameters: list[Name | Vararg] = list(parameters)
        self.body: Block = body

    @staticmethod
    def from_base_definition(
        base: BaseFunctionDefinition, function_name: Name
    ) -> LocalFunctionDefinition:
        return LocalFunctionDefinition(
            base.token, function_name, base.parameters, base.body
        )
