from __future__ import annotations

from typing import Any, Optional

from tumfl.AST import Name
from tumfl.minifier.util import MutableBool, SharedList
from tumfl.minifier.util.replacements import ReplacementCollection, Replacements


class Variable:
    def __init__(self, is_global: bool, preserve: bool) -> None:
        # ideally, we would use sets, but they compare by equality, and all names are equal
        self.writes: list[Name] = []
        self.reads: list[Name] = []
        self.children: dict[str, Variable] = {}
        self.scopes: list[tuple[Scope | Variable, Name]] = []
        self.has_variable_access: MutableBool = MutableBool(False)
        self.is_global: MutableBool = MutableBool(is_global)
        self.preserve: MutableBool = MutableBool(preserve)
        self._shared: SharedList[Variable] = SharedList(self)

    def remove(self, name: Name) -> None:
        if name not in self:
            return
        for i, test in enumerate(self.writes):
            if test is name:
                self.writes.pop(i)
                break
        else:
            for i, test in enumerate(self.reads):
                if test is name:
                    self.reads.pop(i)
                    break
        self.cleanup()

    def add_scope(self, parent: Variable | Scope, name: Name) -> None:
        if (parent, name) not in self.scopes:
            self.scopes.append((parent, name))

    def cleanup(self) -> None:
        if len(self.writes) == 0 and len(self.reads) == 0:
            for scope, name in self.scopes:
                scope.remove_var(name.variable_name)
            self.scopes.clear()

    def __register(self, name: Name) -> None:
        name.set_attribute(self)
        if name.parent_class:
            name.parent_class.set_attribute_if_not_exists(self)

    def add_write(self, write: Name) -> None:
        self.writes.append(write)
        self.__register(write)

    def __contains__(self, item: Any) -> bool:
        # in does not work, as all names are equal
        if any(write is item for write in self.writes):
            return True
        return any(read is item for read in self.reads)

    def add_read(self, read: Name, is_method: bool) -> None:
        if read not in self:
            self.reads.append(read)
            self.__register(read)
        if is_method:
            # do not mess with method invocations
            self.preserve.value = True

    def add_variable(self, name: Name) -> Variable:
        self.children[name.variable_name] = self.children.get(
            name.variable_name, Variable(self.is_global.value, self.preserve.value)
        )
        self.children[name.variable_name].add_scope(self, name)
        return self.children[name.variable_name]

    def remove_var(self, name: str) -> None:
        del self.children[name]

    def __repr__(self) -> str:
        return f"Variable({self.writes=}, {self.reads=}, {self.children=}, {self.has_variable_access=}, {self.is_global=})"

    def is_unused(self) -> bool:
        return len(self.reads) == 0 and all(
            child.is_unused() for child in self.children.values()
        )

    def merge(self, other: Variable) -> None:
        self.writes.extend(other.writes)
        self.reads.extend(other.reads)
        for name, children in other.children.items():
            if name in self.children:
                self.children[name].merge(children)
            else:
                self.children[name] = children
        self.scopes.extend(other.scopes)
        _side_effect = self.has_variable_access or other.has_variable_access
        _side_effect = self.is_global or other.is_global
        _side_effect = self.preserve or other.preserve  # noqa: F841
        # pylint: disable=protected-access
        for obj in self._shared.absorb(other._shared):
            obj.writes = self.writes
            obj.reads = self.reads
            obj.scopes = self.scopes
            obj.children = self.children
            obj.has_variable_access = self.has_variable_access
            obj.is_global = self.is_global
            obj.preserve = self.preserve

    def collect_replacements(self) -> ReplacementCollection:
        if self.preserve:
            return []
        replacements: ReplacementCollection = []
        self_value: int = len(self.writes) + len(self.reads)
        if not self.has_variable_access.value and len(self.writes) <= 1:
            for children in self.children.values():
                new_replacements = children.collect_replacements()
                self_value -= len(new_replacements) - 1
                replacements.extend(new_replacements)
        alias: Optional[Name] = None
        do_replacement: bool = False
        # we can only recover cost-1 from aliases, minus 4 for new variable, =, and ;
        self_acquired_space = (self_value - 1) * len(
            self.scopes[0][1].variable_name
        ) - 4
        if len(self.writes) == 0 and self.is_global.value and self_acquired_space > 0:
            # is a global variable, declare an alias
            alias = self.scopes[0][1]
            do_replacement = True
        elif len(self.writes) > 0 and all(
            isinstance(scope[0], Scope) for scope in self.scopes
        ):
            # is a standard variable, simply rename it
            do_replacement = True
        if do_replacement:
            new_replacement = Replacements(self.reads + self.writes, alias)
            for inner_list in replacements:
                for inner in inner_list:
                    if inner.parent is None:
                        inner.parent = new_replacement
                    if self.writes and inner.after is None:
                        inner.after = self.writes[0]
            replacements.append([new_replacement])
        return replacements


# circular dependency
# pylint: disable=wrong-import-position
from tumfl.minifier.util.scope import Scope
