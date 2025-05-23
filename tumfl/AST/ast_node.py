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
        return generic_str(self, ["parent_class"])

    def __dir(self) -> Generator[str, None, None]:
        return (
            i
            for i in dir(self)
            if not i.startswith("_")
            # ignore "token" for comparison (and parent check)
            and i
            not in [
                "parent_class",
                "token",
                "comment",
                "attributes",
                "file_name",
                "name",
            ]
        )

    def __get_children(self) -> Generator[ASTNode, None, None]:
        from tumfl.AST.statement.local_assign import AttributedName

        for name in self.__dir():
            node: Any = getattr(self, name)
            if isinstance(node, ASTNode):
                yield node
            elif isinstance(node, list):
                for child in node:
                    if isinstance(child, ASTNode):
                        yield child
                    elif isinstance(child, AttributedName):
                        yield child.name
                        if child.attribute is not None:
                            yield child.attribute

    def parent(
        self, parent: Optional[ASTNode], file_name: Optional[Path] = None
    ) -> None:

        self.parent_class = parent
        self.file_name = file_name
        for child in self.__get_children():
            child.parent(self, file_name)

    def replace(self, replacement: ASTNode) -> None:
        """Replaces node in-place"""
        self.__class__ = replacement.__class__  # type: ignore
        self.__dict__.clear()
        self.__dict__.update(replacement.__dict__)
        for child in self.__get_children():
            child.parent_class = self

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

    def set_attribute_if_not_exists(self, value: Any) -> None:
        if type(value) not in self.attributes:
            self.set_attribute(value)

    def get_attribute(self, key: Type[T]) -> Optional[T]:
        return self.attributes.get(key)

    def __hash__(self) -> int:
        return hash(
            tuple(
                var
                for name in self.__dir()
                if not callable(var := getattr(self, name))
                and getattr(var, "__hash__", None)
            )
        )
