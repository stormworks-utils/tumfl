from __future__ import annotations

from itertools import zip_longest
from typing import Any, Optional, Sequence

from tumfl.AST import (
    Assign,
    ASTNode,
    Block,
    ExpFunctionDefinition,
    ExplicitTableField,
    ExpMethodInvocation,
    FunctionDefinition,
    Index,
    IterativeFor,
    LocalAssign,
    LocalFunctionDefinition,
    MethodInvocation,
    Name,
    NamedIndex,
    NamedTableField,
    NumberedTableField,
    NumericFor,
    Statement,
    Table,
    Vararg,
)
from tumfl.basic_walker import NoneWalker
from tumfl.minifier.util import MutableBool, SharedList


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
        assert name in self
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
        assert name.parent_class
        name.parent_class.set_attribute(self)

    def add_write(self, write: Name) -> None:
        self.writes.append(write)
        self.__register(write)

    def __contains__(self, item: Any) -> bool:
        # in does not work, as all names are equal
        if any(write is item for write in self.writes):
            return True
        return any(read is item for read in self.reads)

    def add_read(self, read: Name) -> None:
        if read not in self:
            self.reads.append(read)
            self.__register(read)

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

    def use_variable(self, name: Name) -> Variable:
        if name.variable_name in self.variables:
            self.variables[name.variable_name].add_read(name)
            self.__register(name)
            return self.variables[name.variable_name]
        if self.parent:
            return self.parent.use_variable(name)
        # unknown global
        self.add_variable(name, False, False, False)
        return self.use_variable(name)

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


class GetNames(NoneWalker):
    # pylint: disable=too-many-public-methods
    def __init__(self, ignored_names: Optional[Sequence[str]] = None) -> None:
        super().__init__()
        self.current_scope: Scope = Scope()
        self.scope_initialized: bool = False
        self.has_metatable: bool = False
        self.preserve: bool = False
        self.ignored_names: set[str] = set(ignored_names) if ignored_names else set()

    def push_outer_scope(self) -> None:
        self.scope_initialized = True
        self.push_scope()

    def push_scope(self) -> None:
        self.current_scope = Scope(parent=self.current_scope)

    def pop_scope(self) -> None:
        assert self.current_scope.parent, "Can not pop the root scope"
        self.current_scope = self.current_scope.parent

    def add_var_opt(self, node: ASTNode, global_: bool = False) -> None:
        if isinstance(node, Name) and node.variable_name not in self.ignored_names:
            self.current_scope.add_variable(node, self.preserve, global_)
        elif isinstance(node, NamedIndex):
            self.read_var(node.lhs)
            self.handle_subscript(node.lhs, node.variable_name, True)

    def read_var(self, node: ASTNode) -> None:
        if isinstance(node, Name) and node.variable_name not in self.ignored_names:
            self.current_scope.use_variable(node)
        elif isinstance(node, NamedIndex):
            self.read_var(node.lhs)
            self.handle_subscript(node.lhs, node.variable_name)

    def handle_subscript(
        self, base: ASTNode, extension: ASTNode, assign: bool = False
    ) -> None:
        if (var := base.get_attribute(Variable)) and isinstance(extension, Name):
            new_var = var.add_variable(extension)
            extension.set_attribute(new_var)
            if assign:
                new_var.add_write(extension)
            else:
                new_var.add_read(extension)

    def set_preserve(self, node: Statement) -> None:
        if any("preserve" in comment for comment in node.token.comment):
            self.preserve = True
        elif any("preserve" in comment for comment in node.comment):
            self.preserve = True

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> None:
        self.set_preserve(node)
        last_name: Name = node.names[0]
        self.add_var_opt(last_name, True)
        for name in node.names[1:]:
            self.handle_subscript(last_name, name, True)
            last_name = name
        if node.method_name:
            self.handle_subscript(last_name, node.method_name, True)
        self.preserve = False
        self.push_outer_scope()
        for param in node.parameters:
            self.add_var_opt(param)
        super().visit_FunctionDefinition(node)

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> None:
        self.add_var_opt(node.function_name)
        self.push_outer_scope()
        for param in node.parameters:
            self.add_var_opt(param)
        super().visit_LocalFunctionDefinition(node)

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> None:
        self.push_outer_scope()
        super().visit_ExpFunctionDefinition(node)

    def visit_Name(self, node: Name) -> None:
        if node.variable_name == "setmetatable":
            self.has_metatable = True
        assert node.parent_class
        parent: ASTNode = node.parent_class
        do_it: bool = (
            not isinstance(
                parent,
                (
                    NamedIndex,
                    NamedTableField,
                    ExpMethodInvocation,
                    MethodInvocation,
                    FunctionDefinition,
                    LocalFunctionDefinition,
                ),
            )
            or isinstance(parent, (ExpMethodInvocation, MethodInvocation))
            and node is not parent.method
            or isinstance(parent, NamedIndex)
            and node is not parent.variable_name
            or isinstance(parent, NamedTableField)
            and node is not parent.field_name
            or isinstance(parent, FunctionDefinition)
            and node is not parent.method_name
            and node not in parent.names
            or isinstance(parent, LocalFunctionDefinition)
            and node is not parent.function_name
        )
        if do_it:
            self.read_var(node)

    def visit_Assign(self, node: Assign) -> None:
        self.set_preserve(node)
        for target in node.targets:
            self.add_var_opt(target, True)
        self.preserve = False
        super().visit_Assign(node)

    def visit_LocalAssign(self, node: LocalAssign) -> None:
        for name in node.variable_names:
            self.add_var_opt(name.name)
        super().visit_LocalAssign(node)

    def visit_IterativeFor(self, node: IterativeFor) -> None:
        self.push_outer_scope()
        for name in node.namelist:
            self.add_var_opt(name)
        super().visit_IterativeFor(node)

    def visit_NumericFor(self, node: NumericFor) -> None:
        self.push_outer_scope()
        self.add_var_opt(node.variable_name)
        super().visit_NumericFor(node)

    def visit_Block(self, node: Block) -> None:
        if not self.scope_initialized:
            self.push_scope()
        self.scope_initialized = False
        super().visit_Block(node)
        self.pop_scope()

    def visit_NamedIndex(self, node: NamedIndex) -> None:
        super().visit_NamedIndex(node)
        self.handle_subscript(node.lhs, node.variable_name)

    def visit_NamedTableField(self, node: NamedTableField) -> None:
        assert node.parent_class
        self.handle_subscript(node.parent_class, node.field_name, True)
        super().visit_NamedTableField(node)

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> None:
        super().visit_ExplicitTableField(node)
        assert node.parent_class
        if var := node.parent_class.get_attribute(Variable):
            var.has_variable_access.value = True

    def visit_NumberedTableField(self, node: NumberedTableField) -> None:
        super().visit_NumberedTableField(node)
        assert node.parent_class
        if var := node.parent_class.get_attribute(Variable):
            var.has_variable_access.value = True

    def visit_MethodInvocation(self, node: MethodInvocation) -> None:
        super().visit_MethodInvocation(node)
        self.handle_subscript(node.function, node.method)

    def visit_Index(self, node: Index) -> None:
        super().visit_Index(node)
        if var := node.lhs.get_attribute(Variable):
            var.has_variable_access.value = True

    def visit_Table(self, node: Table) -> None:
        if not node.get_attribute(Variable):
            node.set_attribute(Variable(False, False))
        super().visit_Table(node)


class RemoveName(NoneWalker):
    def visit_Name(self, node: Name) -> None:
        if var := node.get_attribute(Variable):
            var.remove(node)


class RemoveUnused(NoneWalker):
    def __init__(self) -> None:
        super().__init__()
        self.found_any: bool = False
        self.remove: RemoveName = RemoveName()

    def cleanup(self, node: ASTNode) -> bool:
        for comment in node.token.comment:
            if "tumfl" in comment and "preserve" in comment:
                return False
        self.found_any = True
        self.remove(node)
        assert node.parent_class
        node.remove()
        return True

    def visit_Assign(self, node: Assign) -> None:
        if all(
            isinstance(target, Name)
            and (var := target.get_attribute(Variable))
            and var.is_unused()
            for target in node.targets
        ):
            if self.cleanup(node):
                return
        super().visit_Assign(node)

    def visit_LocalAssign(self, node: LocalAssign) -> None:
        if all(
            (var := name.name.get_attribute(Variable)) and var.is_unused()
            for name in node.variable_names
        ):
            if self.cleanup(node):
                return
        super().visit_LocalAssign(node)

    def cleanup_params(self, params: list[Name | Vararg]) -> None:
        if all(not isinstance(param, Vararg) for param in params):
            for i in range(len(params) - 1, -1, -1):
                if (var := params[i].get_attribute(Variable)) and var.is_unused():
                    if self.cleanup(params[i]):
                        params.pop(i)
                    else:
                        break
                else:
                    break

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> None:
        if (var := node.names[0].get_attribute(Variable)) and var.is_unused():
            if self.cleanup(node):
                return
        self.cleanup_params(node.parameters)
        super().visit_FunctionDefinition(node)

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> None:
        if (var := node.function_name.get_attribute(Variable)) and var.is_unused():
            if self.cleanup(node):
                return
        self.cleanup_params(node.parameters)
        super().visit_LocalFunctionDefinition(node)

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> None:
        self.cleanup_params(node.parameters)
        super().visit_ExpFunctionDefinition(node)


def remove_unused_names(node: ASTNode, names: GetNames) -> None:
    remove = RemoveUnused()
    remove.found_any = True
    while remove.found_any:
        remove.found_any = False
        remove(node)
        names.current_scope.cleanup_scopes()
