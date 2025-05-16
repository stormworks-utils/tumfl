from __future__ import annotations

from typing import Optional

from tumfl.AST import Name


class Replacements:
    def __init__(self, targets: list[Name], original: Optional[Name]):
        self.targets: list[Name] = targets
        for target in targets:
            target.set_attribute(self)
        self.original: Optional[Name] = original
        self.parent: Optional[Replacements] = None
        self.replacement: Optional[str] = None
        self.after: Optional[Name] = None

    def value(self) -> int:
        return len(self.targets)

    def __repr__(self) -> str:
        return f"Replacements({self.targets=}, {self.original=})"


ReplacementCollection = list[list[Replacements]]


def key_function(replacements: list[Replacements]) -> int:
    return sum(replacement.value() for replacement in replacements)
