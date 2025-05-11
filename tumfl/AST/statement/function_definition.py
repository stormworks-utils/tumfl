from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import BaseFunctionDefinition, Block, Name, Vararg
    from tumfl.Token import Token


class FunctionDefinition(Statement):
    """Definition of a lua function, NOT local"""

    def __init__(
        self,
        token: Token,
        names: Sequence[Name],
        method_name: Optional[Name],
        parameters: Sequence[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "FunctionDefinition")
        self.names: list[Name] = list(names)
        self.method_name: Optional[Name] = method_name
        self.parameters: list[Name | Vararg] = list(parameters)
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
