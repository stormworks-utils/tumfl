from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Any, Generator, Generic, Optional, TypeVar

from tumfl.Token import Token
from tumfl.utils import generic_str

T = TypeVar("T")


class ASTNode(ABC, Generic[T]):
    """Base class for all AST nodes"""

    def __init__(self, token: Token, name: str) -> None:
        self.name: str = name
        self.token: Token = token
        self.parent_class: Optional[ASTNode] = None
        self.file_name: Optional[Path] = None
        self.attributes: Optional[T] = None

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
            for i in dir(self)
            if not i.startswith("__")
            # ignore "token" for comparison (and parent check)
            and i
            not in ["replace", "parent", "parent_class", "var", "token", "comment"]
        )

    def parent(
        self, parent: Optional[ASTNode], file_name: Optional[Path] = None
    ) -> None:
        self.parent_class = parent
        self.file_name = file_name
        for i in self.__dir():
            node: Any = getattr(self, i)
            if isinstance(node, ASTNode):
                node.parent(self, file_name)
            elif (
                isinstance(node, list)
                and len(node) > 0
                and isinstance(node[0], ASTNode)
            ):
                for node in node:
                    node.parent(self, file_name)

    def replace_child(self, to_replace: ASTNode, replacement: ASTNode) -> None:
        for i in self.__dir():
            node: Any = getattr(self, i)
            if node is to_replace:
                setattr(self, i, replacement)
                return
            if isinstance(node, list):
                for j, element in enumerate(node):
                    if element is to_replace:
                        node[j] = replacement
                        return
