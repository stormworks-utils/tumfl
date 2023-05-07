from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generator, Optional

from tumfl.Token import Token
from tumfl.utils import generic_str


class ASTNode(ABC):
    """Base class for all AST nodes"""

    def __init__(self, token: Token, name: str) -> None:
        self.name: str = name
        self.token: Token = token
        self.parent_class: Optional[ASTNode] = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return all(
            callable(getattr(self, i)) or getattr(self, i) == getattr(other, i)
            for i in self.__dir()
        )

    def __repr__(self) -> str:
        return generic_str(self, ["replace", "parent", "parent_class"])

    def __dir(self) -> Generator[str, None, None]:
        return (
            i
            for i in self.__dir__()
            if not i.startswith("__")
            # ignore "token" for comparison (and parent check)
            and i not in ["replace", "parent", "parent_class", "var", "token"]
        )

    def parent(self, parent: ASTNode) -> None:
        self.parent_class = parent
        for i in self.__dir():
            node: Any = getattr(self, i)
            if isinstance(node, ASTNode):
                node.parent(self)
