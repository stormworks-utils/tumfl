from __future__ import annotations

from .Statement import Statement
from .Block import Block
from tumfl.AST.Expression import Vararg
from tumfl.Token import Token, TokenType


class LocalFunctionDefinition(Statement):
    """Definition for a local function"""

    def __init__(
        self,
        token: Token,
        comment: list[str],
        function_name: str,
        parameters: list[str | Vararg],
        body: Block,
    ):
        super().__init__(token, "LocalFunctionDefinition", comment)
        self.function_name: str = function_name
        self.parameters: list[str | Vararg] = parameters
        self.body: Block = body
