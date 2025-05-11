from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from .block import Block

if TYPE_CHECKING:
    from tumfl.AST import Expression, Statement
    from tumfl.Token import Token


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
