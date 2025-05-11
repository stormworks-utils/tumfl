from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from tumfl.Token import Token

from .ast_node import ASTNode

if TYPE_CHECKING:
    from .expression.name import Name
    from .expression.vararg import Vararg
    from .statement.block import Block


class BaseFunctionDefinition(ASTNode, ABC):
    """Definition of a lua function, NOT local"""

    def __init__(
        self,
        token: Token,
        parameters: list[Name | Vararg],
        body: Block,
    ):
        super().__init__(token, "BaseFunctionDefinition")
        self.parameters: list[Name | Vararg] = parameters
        self.body: Block = body
