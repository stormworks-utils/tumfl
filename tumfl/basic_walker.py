from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, NoReturn, TypeVar

from .AST import *

T = TypeVar("T")


class NodeVisitor(Generic[T]):
    def visit(self, node: ASTNode) -> T:
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> NoReturn:
        raise RuntimeError(f"No visit_{type(node).__name__} method")


class BasicWalker(NodeVisitor, Generic[T], ABC):
    # pylint: disable=unused-argument,too-many-public-methods
    def visit_BinOp(self, node: BinOp) -> T:
        self.visit(node.right)
        return self.visit(node.left)

    @abstractmethod
    def visit_Boolean(self, node: Boolean) -> T:
        raise NotImplementedError

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> T:
        ret: T = self.visit(node.function)
        for argument in node.arguments:
            self.visit(argument)
        return ret

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> T:
        for parameter in node.parameters:
            self.visit(parameter)
        return self.visit(node.body)

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> T:
        self.visit(node.function)
        ret: T = self.visit(node.method)
        for argument in node.arguments:
            self.visit(argument)
        return ret

    def visit_Index(self, node: Index) -> T:
        self.visit(node.lhs)
        return self.visit(node.variable_name)

    @abstractmethod
    def visit_Name(self, node: Name) -> T:
        raise NotImplementedError

    def visit_NamedIndex(self, node: NamedIndex) -> T:
        self.visit(node.lhs)
        return self.visit(node.variable_name)

    @abstractmethod
    def visit_Nil(self, node: Nil) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_Number(self, node: Number) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_String(self, node: String) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_Table(self, node: Table) -> T:
        raise NotImplementedError

    def visit_UnOp(self, node: UnOp) -> T:
        return self.visit(node.right)

    @abstractmethod
    def visit_Vararg(self, node: Vararg) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_Assign(self, node: Assign) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_Block(self, node: Block) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_Break(self, node: Break) -> T:
        raise NotImplementedError

    def visit_Chunk(self, node: Chunk) -> T:
        return self.visit_Block(node)

    def visit_FunctionCall(self, node: FunctionCall) -> T:
        ret: T = self.visit(node.function)
        for argument in node.arguments:
            self.visit(argument)
        return ret

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> T:
        for name in node.names:
            self.visit(name)
        if node.method_name:
            self.visit(node.method_name)
        for parameter in node.parameters:
            self.visit(parameter)
        return self.visit(node.body)

    @abstractmethod
    def visit_Goto(self, node: Goto) -> T:
        raise NotImplementedError

    def visit_If(self, node: If) -> T:
        self.visit(node.test)
        ret: T = self.visit(node.true)
        if node.false:
            self.visit(node.false)
        return ret

    def visit_IterativeFor(self, node: IterativeFor) -> T:
        for name in node.namelist:
            self.visit(name)
        for expression in node.explist:
            self.visit(expression)
        return self.visit(node.body)

    @abstractmethod
    def visit_Label(self, node: Label) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_LocalAssign(self, node: LocalAssign) -> T:
        raise NotImplementedError

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> T:
        self.visit(node.function_name)
        for parameter in node.parameters:
            self.visit(parameter)
        return self.visit(node.body)

    def visit_MethodInvocation(self, node: MethodInvocation) -> T:
        ret: T = self.visit(node.function)
        self.visit(node.method)
        for argument in node.arguments:
            self.visit(argument)
        return ret

    def visit_NumericFor(self, node: NumericFor) -> T:
        self.visit(node.variable_name)
        self.visit(node.start)
        self.visit(node.stop)
        if node.step:
            self.visit(node.step)
        return self.visit(node.body)

    def visit_Repeat(self, node: Repeat) -> T:
        self.visit(node.condition)
        return self.visit(node.body)

    @abstractmethod
    def visit_Semicolon(self, node: Semicolon) -> T:
        raise NotImplementedError

    def visit_While(self, node: While) -> T:
        self.visit(node.condition)
        return self.visit(node.body)

    def visit_NamedTableField(self, node: NamedTableField) -> T:
        self.visit(node.field_name)
        return self.visit(node.value)

    def visit_NumberedTableField(self, node: NumberedTableField) -> T:
        return self.visit(node.value)

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> T:
        self.visit(node.at)
        return self.visit(node.value)


class NoneWalker(BasicWalker[None]):
    def visit_Boolean(self, node: Boolean) -> None:
        pass

    def visit_Name(self, node: Name) -> None:
        pass

    def visit_Nil(self, node: Nil) -> None:
        pass

    def visit_Number(self, node: Number) -> None:
        pass

    def visit_String(self, node: String) -> None:
        pass

    def visit_Table(self, node: Table) -> None:
        for field in node.fields:
            self.visit(field)

    def visit_Vararg(self, node: Vararg) -> None:
        pass

    def visit_Assign(self, node: Assign) -> None:
        for target in node.targets:
            self.visit(target)
        if node.expressions:
            for expr in node.expressions:
                self.visit(expr)

    def visit_Block(self, node: Block) -> None:
        for stmt in node.statements:
            self.visit(stmt)
        if node.returns:
            for expr in node.returns:
                self.visit(expr)

    def visit_Break(self, node: Break) -> None:
        pass

    def visit_Goto(self, node: Goto) -> None:
        self.visit(node.label_name)

    def visit_Label(self, node: Label) -> None:
        self.visit(node.label_name)

    def visit_LocalAssign(self, node: LocalAssign) -> None:
        for var in node.variable_names:
            self.visit(var.name)

    def visit_Semicolon(self, node: Semicolon) -> None:
        pass
