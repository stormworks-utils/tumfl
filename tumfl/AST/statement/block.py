from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from .statement import Statement

if TYPE_CHECKING:
    from tumfl.AST import Expression
    from tumfl.Token import Token


class Block(Statement):
    """A block consisting of statements"""

    def __init__(
        self,
        token: Token,
        statements: Sequence[Statement],
        returns: Optional[Sequence[Expression]],
    ):
        super().__init__(token, "Block")
        self.statements: list[Statement] = list(statements)
        self.returns: Optional[list[Expression]] = (
            list(returns) if returns is not None else None
        )
