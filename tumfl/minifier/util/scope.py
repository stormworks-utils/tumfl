from __future__ import annotations

from itertools import zip_longest
from typing import Optional

from tumfl.AST import Name
from tumfl.minifier.util.replacements import ReplacementCollection, key_function
from tumfl.minifier.util.variable import Variable


class Scope:
    def __init__(self, parent: Optional[Scope] = None) -> None:
        self.parent: Optional[Scope] = None
        self.root: Scope = self
        self.level: int = 0
        self.children: list[Scope] = []
        self.variables: dict[str, Variable] = {}
        if parent:
            self.add_parent(parent)

    def add_parent(self, parent: Scope) -> None:
        self.parent = parent
        parent.children.append(self)
        self.root = parent.root
        self.level = parent.level + 1

    def __register(self, node: Name) -> None:
        node.set_attribute(self)

    def add_variable(
        self, name: Name, preserve: bool, global_: bool = False, add_write: bool = True
    ) -> Variable:
        if global_:
            if name.variable_name in self.variables:
                var = self.variables[name.variable_name]
                var.add_write(name)
                return var
            if self.parent:
                return self.parent.add_variable(name, preserve, global_, add_write)
            return self.root.add_variable(name, preserve)
        self.variables[name.variable_name] = self.variables.get(
            name.variable_name, Variable(self.root is self, preserve)
        )
        self.variables[name.variable_name].add_scope(self, name)
        if add_write:
            self.variables[name.variable_name].add_write(name)
        self.__register(name)
        return self.variables[name.variable_name]

    def use_variable(self, name: Name, is_method: bool) -> Variable:
        if name.variable_name in self.variables:
            self.variables[name.variable_name].add_read(name, is_method)
            self.__register(name)
            return self.variables[name.variable_name]
        if self.parent:
            return self.parent.use_variable(name, is_method)
        # unknown global
        self.add_variable(name, False, False, False)
        return self.use_variable(name, is_method)

    def __repr__(self) -> str:
        return f"Scope({self.level=}, {self.variables=}, {self.children=})"

    def cleanup_scopes(self) -> None:
        for var in self.variables.values():
            var.cleanup()
        for child in range(len(self.children) - 1, -1, -1):
            self.children[child].cleanup_scopes()
        if len(self.variables) == 0 and len(self.children) == 0 and self.parent:
            self.parent.children.remove(self)

    def remove_var(self, name: str) -> None:
        del self.variables[name]

    def collect_replacements(self) -> ReplacementCollection:
        result: ReplacementCollection = []
        for var in self.variables.values():
            result.extend(var.collect_replacements())

        to_evaluate: list[ReplacementCollection] = []
        for child in self.children:
            to_evaluate.append(child.collect_replacements())
        result.extend(
            sum(group, []) for group in zip_longest(*to_evaluate, fillvalue=[])
        )

        result.sort(key=key_function, reverse=True)
        return result
