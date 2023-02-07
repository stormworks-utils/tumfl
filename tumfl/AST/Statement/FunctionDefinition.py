from __future__ import annotations
from typing import Optional

from .Statement import Statement
from .Block import Block
from tumfl.AST.Expression import Vararg
from tumfl.Token import Token, TokenType


class FunctionDefinition(Statement):
    """Definition of a lua function, NOT local"""

    def __init__(
        self,
        token: Token,
        comment: list[str],
        names: list[str],
        method_name: Optional[str],
        parameters: list[str | Vararg],
        body: Block,
    ):
        super().__init__(token, "FunctionDefinition", comment)
        self.names: list[str] = names
        self.method_name: Optional[str] = method_name
        self.parameters: list[str | Vararg] = parameters
        self.body: Block = body
