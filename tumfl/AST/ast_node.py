from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Any, Generator, Optional, Type, TypeVar
from weakref import ReferenceType, ref

from tumfl.Token import Token
from tumfl.utils import generic_str

T = TypeVar("T")


class ASTNode(ABC):
    """Base class for all AST nodes"""

    def __init__(self, token: Token, name: str) -> None:
        self.name: str = name
        self.token: Token = token
        self._parent_class: Optional[ReferenceType[ASTNode]] = None
        self.file_name: Optional[Path] = None
        self.attributes: dict[Type[Any], Any] = {}

    @property
    def parent_class(self) -> Optional[ASTNode]:
        return None if self._parent_class is None else self._parent_class()

    @parent_class.setter
    def parent_class(self, value: Optional[ASTNode]) -> None:
        self._parent_class = ref(value) if value is not None else None

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
            if not i.startswith("_")
            # ignore "token" for comparison (and parent check)
            and i
            not in [
                "replace",
                "parent",
                "remove",
                "set_attribute",
                "get_attribute",
                "parent_class",
                "var",
                "token",
                "comment",
                "attributes",
                "file_name",
                "name",
            ]
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
                    assert isinstance(node, ASTNode)
                    node.parent(self, file_name)

    def replace(self, replacement: ASTNode) -> None:
        """Replaces node in-place"""
        self.__class__ = replacement.__class__  # type: ignore
        self.__dict__.clear()
        self.__dict__.update(replacement.__dict__)

    def remove(self) -> None:
        """Removes a child by replacing it with Semicolon or Boolean"""
        # Previously, this did remove the child node, but that leads
        # to issues when iterating over the children
        from tumfl.AST import Boolean, Semicolon, Statement

        replacement: ASTNode
        if isinstance(self, Statement):
            replacement = Semicolon(self.token)
        else:
            replacement = Boolean(self.token, False)
        replacement.parent(self.parent_class, self.file_name)
        self.replace(replacement)

    def set_attribute(self, value: Any) -> None:
        self.attributes[type(value)] = value

    def get_attribute(self, key: Type[T]) -> Optional[T]:
        return self.attributes.get(key)
