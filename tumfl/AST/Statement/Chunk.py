from __future__ import annotations

from typing import Optional, Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Block import Block
from .Statement import Statement


class Chunk(Block):
    """Same as block, but individually executable."""

    def __init__(
        self,
        token: Token,
        statements: Sequence[Statement],
        returns: Optional[Sequence[Expression]],
    ):
        super().__init__(token, statements, returns)
        self.name = "Chunk"
