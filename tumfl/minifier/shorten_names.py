from __future__ import annotations

from typing import Optional, Sequence

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
from tumfl.minifier.util.remove_name import RemoveName
from tumfl.minifier.util.scope import Scope
from tumfl.minifier.util.variable import Variable


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
            self.current_scope.use_variable(node, False)
        elif isinstance(node, NamedIndex):
            self.read_var(node.lhs)
            self.handle_subscript(node.lhs, node.variable_name)

    def handle_subscript(
        self,
        base: ASTNode,
        extension: ASTNode,
        assign: bool = False,
        is_method: bool = False,
    ) -> None:
        if (var := base.get_attribute(Variable)) and isinstance(extension, Name):
            new_var = var.add_variable(extension)
            extension.set_attribute_if_not_exists(new_var)
            if assign:
                new_var.add_write(extension)
            else:
                new_var.add_read(extension, is_method)

    def set_preserve(self, node: Statement) -> None:
        if any("preserve" in comment for comment in node.token.comment):
            self.preserve = True
        elif any("preserve" in comment for comment in node.comment):
            self.preserve = True

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> None:
        self.set_preserve(node)
        last_name: Name = node.names[0]
        self.add_var_opt(last_name, global_=True)
        for name in node.names[1:]:
            self.handle_subscript(last_name, name, assign=True)
            last_name = name
        if node.method_name:
            self.handle_subscript(
                last_name, node.method_name, assign=True, is_method=True
            )
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
        self.handle_subscript(node.function, node.method, is_method=True)

    def visit_Index(self, node: Index) -> None:
        super().visit_Index(node)
        if var := node.lhs.get_attribute(Variable):
            var.has_variable_access.value = True

    def visit_Table(self, node: Table) -> None:
        if not node.get_attribute(Variable):
            node.set_attribute_if_not_exists(Variable(False, False))
        super().visit_Table(node)


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
        if node.parent_class:
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
