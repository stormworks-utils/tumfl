from __future__ import annotations

from typing import Optional

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class Chunk(Block):
    """Same as block, but individually executable."""

    def __init__(
        self,
        token: Token,
        statements: list[Statement],
        returns: Optional[list[Expression]],
    ):
        super().__init__(token, statements, returns)
        self.name = "Chunk"
