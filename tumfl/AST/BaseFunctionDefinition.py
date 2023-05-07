from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from tumfl.Token import Token

from .ASTNode import ASTNode

if TYPE_CHECKING:
    from .Expression.Name import Name
    from .Expression.Vararg import Vararg
    from .Statement.Block import Block


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
