from __future__ import annotations
from abc import ABC

from .ASTNode import ASTNode
from .Statement.Block import Block
from .Expression.Name import Name
from .Expression.Vararg import Vararg
from tumfl.Token import Token, TokenType


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
