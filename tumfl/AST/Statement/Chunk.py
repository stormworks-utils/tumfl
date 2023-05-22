from __future__ import annotations

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
        returns: list[Expression],
    ):
        super().__init__(token, statements, returns)
        self.name = "Chunk"
