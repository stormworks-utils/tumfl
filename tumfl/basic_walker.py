from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, NoReturn, Optional, TypeVar

from .AST import *

T = TypeVar("T")


class NodeVisitor(Generic[T]):
    def visit(self, node: ASTNode) -> T:
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> NoReturn:
        raise RuntimeError(f"No visit_{type(node).__name__} method")

    def __call__(self, node: ASTNode) -> T:
        return self.visit(node)


class BasicWalker(NodeVisitor[T], ABC):
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
            if var.attribute:
                self.visit(var.attribute)
        if node.expressions:
            for expr in node.expressions:
                self.visit(expr)

    def visit_Semicolon(self, node: Semicolon) -> None:
        pass


V = TypeVar("V")


class OptionalWalker(BasicWalker[Optional[V]]):
    # pylint: disable=too-many-public-methods
    def visit_BinOp(self, node: BinOp) -> Optional[V]:
        if ret := self.visit(node.right):
            return ret
        return self.visit(node.left)

    def visit_Boolean(self, node: Boolean) -> Optional[V]:
        return None

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> Optional[V]:
        if ret := self.visit(node.function):
            return ret
        for argument in node.arguments:
            if ret := self.visit(argument):
                return ret
        return None

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> Optional[V]:
        for parameter in node.parameters:
            if ret := self.visit(parameter):
                return ret
        return self.visit(node.body)

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> Optional[V]:
        if ret := self.visit(node.function):
            return ret
        if ret := self.visit(node.method):
            return ret
        for argument in node.arguments:
            if ret := self.visit(argument):
                return ret
        return None

    def visit_Index(self, node: Index) -> Optional[V]:
        if ret := self.visit(node.lhs):
            return ret
        return self.visit(node.variable_name)

    def visit_Name(self, node: Name) -> Optional[V]:
        return None

    def visit_NamedIndex(self, node: NamedIndex) -> Optional[V]:
        if ret := self.visit(node.lhs):
            return ret
        return self.visit(node.variable_name)

    def visit_Nil(self, node: Nil) -> Optional[V]:
        return None

    def visit_Number(self, node: Number) -> Optional[V]:
        return None

    def visit_String(self, node: String) -> Optional[V]:
        return None

    def visit_Table(self, node: Table) -> Optional[V]:
        return None

    def visit_Vararg(self, node: Vararg) -> Optional[V]:
        return None

    def visit_Assign(self, node: Assign) -> Optional[V]:
        return None

    def visit_Block(self, node: Block) -> Optional[V]:
        return None

    def visit_Break(self, node: Break) -> Optional[V]:
        return None

    def visit_FunctionCall(self, node: FunctionCall) -> Optional[V]:
        if ret := self.visit(node.function):
            return ret
        for argument in node.arguments:
            if ret := self.visit(argument):
                return ret
        return None

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> Optional[V]:
        for name in node.names:
            if ret := self.visit(name):
                return ret
        if node.method_name:
            if ret := self.visit(node.method_name):
                return ret
        for parameter in node.parameters:
            if ret := self.visit(parameter):
                return ret
        return self.visit(node.body)

    def visit_Goto(self, node: Goto) -> Optional[V]:
        return None

    def visit_If(self, node: If) -> Optional[V]:
        if ret := self.visit(node.test):
            return ret
        if ret := self.visit(node.true):
            return ret
        if node.false:
            if ret := self.visit(node.false):
                return ret
        return None

    def visit_IterativeFor(self, node: IterativeFor) -> Optional[V]:
        for name in node.namelist:
            if ret := self.visit(name):
                return ret
        for expression in node.explist:
            if ret := self.visit(expression):
                return ret
        return self.visit(node.body)

    def visit_Label(self, node: Label) -> Optional[V]:
        return None

    def visit_LocalAssign(self, node: LocalAssign) -> Optional[V]:
        return None

    def visit_LocalFunctionDefinition(
        self, node: LocalFunctionDefinition
    ) -> Optional[V]:
        if ret := self.visit(node.function_name):
            return ret
        for parameter in node.parameters:
            if ret := self.visit(parameter):
                return ret
        return self.visit(node.body)

    def visit_MethodInvocation(self, node: MethodInvocation) -> Optional[V]:
        if ret := self.visit(node.function):
            return ret
        if ret := self.visit(node.method):
            return ret
        for argument in node.arguments:
            if ret := self.visit(argument):
                return ret
        return None

    def visit_NumericFor(self, node: NumericFor) -> Optional[V]:
        if ret := self.visit(node.variable_name):
            return ret
        if ret := self.visit(node.start):
            return ret
        if ret := self.visit(node.stop):
            return ret
        if node.step:
            if ret := self.visit(node.step):
                return ret
        return self.visit(node.body)

    def visit_Repeat(self, node: Repeat) -> Optional[V]:
        if ret := self.visit(node.condition):
            return ret
        return self.visit(node.body)

    def visit_Semicolon(self, node: Semicolon) -> Optional[V]:
        return None

    def visit_While(self, node: While) -> Optional[V]:
        if ret := self.visit(node.condition):
            return ret
        return self.visit(node.body)

    def visit_NamedTableField(self, node: NamedTableField) -> Optional[V]:
        if ret := self.visit(node.field_name):
            return ret
        return self.visit(node.value)

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> Optional[V]:
        if ret := self.visit(node.at):
            return ret
        return self.visit(node.value)


class AggregatingWalker(BasicWalker[T], ABC):
    # pylint: disable=unused-argument,too-many-public-methods
    @abstractmethod
    def aggregation_function(self, a: T, b: T) -> T:
        """Function to aggregate two values"""
        raise NotImplementedError

    @abstractmethod
    def default_value(self) -> T:
        """Default value for the aggregation"""
        raise NotImplementedError

    def visit_BinOp(self, node: BinOp) -> T:
        return self.aggregation_function(self.visit(node.right), self.visit(node.left))

    def visit_Boolean(self, node: Boolean) -> T:
        return self.default_value()

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> T:
        ret: T = self.visit(node.function)
        for argument in node.arguments:
            ret = self.aggregation_function(ret, self.visit(argument))
        return ret

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> T:
        ret: T = self.default_value()
        for parameter in node.parameters:
            ret = self.aggregation_function(ret, self.visit(parameter))
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> T:
        ret: T = self.visit(node.function)
        ret = self.aggregation_function(ret, self.visit(node.method))
        for argument in node.arguments:
            ret = self.aggregation_function(ret, self.visit(argument))
        return ret

    def visit_Index(self, node: Index) -> T:
        return self.aggregation_function(
            self.visit(node.lhs), self.visit(node.variable_name)
        )

    def visit_Name(self, node: Name) -> T:
        return self.default_value()

    def visit_NamedIndex(self, node: NamedIndex) -> T:
        return self.aggregation_function(
            self.visit(node.lhs), self.visit(node.variable_name)
        )

    def visit_Nil(self, node: Nil) -> T:
        return self.default_value()

    def visit_Number(self, node: Number) -> T:
        return self.default_value()

    def visit_String(self, node: String) -> T:
        return self.default_value()

    def visit_Table(self, node: Table) -> T:
        ret: T = self.default_value()
        for field in node.fields:
            ret = self.aggregation_function(ret, self.visit(field))
        return ret

    def visit_UnOp(self, node: UnOp) -> T:
        return self.visit(node.right)

    def visit_Vararg(self, node: Vararg) -> T:
        return self.default_value()

    def visit_Assign(self, node: Assign) -> T:
        ret: T = self.default_value()
        for target in node.targets:
            ret = self.aggregation_function(ret, self.visit(target))
        for expr in node.expressions:
            ret = self.aggregation_function(ret, self.visit(expr))
        return ret

    def visit_Block(self, node: Block) -> T:
        ret: T = self.default_value()
        for stmt in node.statements:
            ret = self.aggregation_function(ret, self.visit(stmt))
        if node.returns:
            for expr in node.returns:
                ret = self.aggregation_function(ret, self.visit(expr))
        return ret

    def visit_Break(self, node: Break) -> T:
        return self.default_value()

    def visit_Chunk(self, node: Chunk) -> T:
        return self.visit_Block(node)

    def visit_FunctionCall(self, node: FunctionCall) -> T:
        ret: T = self.visit(node.function)
        for argument in node.arguments:
            ret = self.aggregation_function(ret, self.visit(argument))
        return ret

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> T:
        ret: T = self.default_value()
        for name in node.names:
            ret = self.aggregation_function(ret, self.visit(name))
        if node.method_name:
            ret = self.aggregation_function(ret, self.visit(node.method_name))
        for parameter in node.parameters:
            ret = self.aggregation_function(ret, self.visit(parameter))
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_Goto(self, node: Goto) -> T:
        return self.default_value()

    def visit_If(self, node: If) -> T:
        ret: T = self.visit(node.test)
        ret = self.aggregation_function(ret, self.visit(node.true))
        if node.false:
            ret = self.aggregation_function(ret, self.visit(node.false))
        return ret

    def visit_IterativeFor(self, node: IterativeFor) -> T:
        ret: T = self.default_value()
        for name in node.namelist:
            ret = self.aggregation_function(ret, self.visit(name))
        for expression in node.explist:
            ret = self.aggregation_function(ret, self.visit(expression))
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_Label(self, node: Label) -> T:
        return self.default_value()

    def visit_LocalAssign(self, node: LocalAssign) -> T:
        ret: T = self.default_value()
        for var in node.variable_names:
            ret = self.aggregation_function(ret, self.visit(var.name))
            if var.attribute:
                ret = self.aggregation_function(ret, self.visit(var.attribute))
        if node.expressions:
            for expr in node.expressions:
                ret = self.aggregation_function(ret, self.visit(expr))
        return ret

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> T:
        ret: T = self.visit(node.function_name)
        for parameter in node.parameters:
            ret = self.aggregation_function(ret, self.visit(parameter))
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_MethodInvocation(self, node: MethodInvocation) -> T:
        ret: T = self.visit(node.function)
        ret = self.aggregation_function(ret, self.visit(node.method))
        for argument in node.arguments:
            ret = self.aggregation_function(ret, self.visit(argument))
        return ret

    def visit_NumericFor(self, node: NumericFor) -> T:
        ret: T = self.visit(node.variable_name)
        ret = self.aggregation_function(ret, self.visit(node.start))
        ret = self.aggregation_function(ret, self.visit(node.stop))
        if node.step:
            ret = self.aggregation_function(ret, self.visit(node.step))
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_Repeat(self, node: Repeat) -> T:
        return self.aggregation_function(
            self.visit(node.condition), self.visit(node.body)
        )

    def visit_Semicolon(self, node: Semicolon) -> T:
        return self.default_value()

    def visit_While(self, node: While) -> T:
        ret: T = self.visit(node.condition)
        return self.aggregation_function(ret, self.visit(node.body))

    def visit_NamedTableField(self, node: NamedTableField) -> T:
        ret: T = self.visit(node.field_name)
        return self.aggregation_function(ret, self.visit(node.value))

    def visit_NumberedTableField(self, node: NumberedTableField) -> T:
        return self.visit(node.value)

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> T:
        ret: T = self.visit(node.at)
        return self.aggregation_function(ret, self.visit(node.value))
