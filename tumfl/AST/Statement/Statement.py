from __future__ import annotations

from abc import ABC

from tumfl.AST.ASTNode import ASTNode
from tumfl.Token import Token


class Statement(ASTNode, ABC):
    """Baseclass for all statements, must contain comments"""

    def __init__(self, token: Token, name: str):
        super().__init__(token, name)
        self.comment: list[str] = token.comment
