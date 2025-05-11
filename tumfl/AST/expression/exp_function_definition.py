from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .expression import Expression

if TYPE_CHECKING:
    from tumfl.AST import BaseFunctionDefinition, Block, Name, Vararg
    from tumfl.Token import Token


class ExpFunctionDefinition(Expression):
    """Definition of a lua function expression"""

    def __init__(
        self,
        token: Token,
        parameters: Sequence[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "ExpFunctionDefinition")
        self.parameters: list[Name | Vararg] = list(parameters)
        self.body: Block = body

    @staticmethod
    def from_base_definition(
        base: BaseFunctionDefinition,
    ) -> ExpFunctionDefinition:
        return ExpFunctionDefinition(base.token, base.parameters, base.body)
