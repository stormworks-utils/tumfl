from __future__ import annotations

from typing import Optional

from typing_extensions import Sequence

from tumfl.AST.Expression.Expression import Expression
from tumfl.Token import Token

from .Statement import Statement


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
