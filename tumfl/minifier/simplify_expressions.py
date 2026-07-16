from __future__ import annotations

from typing import Optional

from tumfl.AST import (
    ASTNode,
    BinaryOperand,
    BinOp,
    Block,
    Boolean,
    ExpMethodInvocation,
    If,
    MethodInvocation,
    Name,
    NamedIndex,
    NamedTableField,
    UnaryOperand,
    UnOp,
)
from tumfl.basic_walker import AggregatingWalker, NoneWalker

from ..to_lua_type import to_lua_type
from ..to_python_type import ToPythonType
from .util.remove_name import RemoveName


class ReplaceName(NoneWalker):
    def __init__(self, replacements: dict[Name, Name]) -> None:
        super().__init__()
        self.replacements: dict[Name, Name] = replacements

    def visit_Name(self, node: Name) -> None:
        if node in self.replacements:
            parent: Optional[ASTNode] = node.parent_class
            if isinstance(parent, NamedIndex) and node is not parent.lhs:
                return
            if (
                isinstance(parent, (MethodInvocation, ExpMethodInvocation))
                and node is not parent.function
            ):
                return
            if isinstance(parent, NamedTableField) and node is not parent.value:
                return
            node.replace(self.replacements[node])


class HasReturn(AggregatingWalker[bool]):
    def aggregation_function(self, a: bool, b: bool) -> bool:
        return a or b

    def default_value(self) -> bool:
        return False

    def visit_Block(self, node: Block) -> bool:
        return bool(node.returns) or super().visit_Block(node)


class Simplify(NoneWalker):
    def __init__(self) -> None:
        super().__init__()
        self.has_return = HasReturn()
        self.remove_name = RemoveName()
        self.to_python = ToPythonType()

    def visit_BinOp(self, node: BinOp) -> None:
        super().visit_BinOp(node)
        if (result := self.to_python.visit(node)) is not None:
            as_lua = to_lua_type(result)
            node.replace(as_lua)

    def visit_UnOp(self, node: UnOp) -> None:
        super().visit_UnOp(node)
        if (result := self.to_python.visit(node)) is not None:
            as_lua = to_lua_type(result)
            node.replace(as_lua)
        elif node.op == UnaryOperand.NOT:
            if isinstance(node.right, BinOp):
                new_op: Optional[BinaryOperand] = None
                if node.right.op == BinaryOperand.EQUALS:
                    new_op = BinaryOperand.NOT_EQUALS
                elif node.right.op == BinaryOperand.NOT_EQUALS:
                    new_op = BinaryOperand.EQUALS
                elif node.right.op == BinaryOperand.GREATER_THAN:
                    new_op = BinaryOperand.LESS_EQUALS
                elif node.right.op == BinaryOperand.GREATER_EQUALS:
                    new_op = BinaryOperand.LESS_THAN
                elif node.right.op == BinaryOperand.LESS_THAN:
                    new_op = BinaryOperand.GREATER_EQUALS
                elif node.right.op == BinaryOperand.LESS_EQUALS:
                    new_op = BinaryOperand.GREATER_THAN
                if new_op is not None:
                    node.right.op = new_op
                    node.replace(node.right)
            elif isinstance(node.right, UnOp) and node.right.op == UnaryOperand.NOT:
                node.replace(node.right.right)
        elif node.op == UnaryOperand.MINUS:
            if isinstance(node.right, BinOp):
                if node.right.op in (BinaryOperand.PLUS, BinaryOperand.MINUS):
                    node.right.op = (
                        BinaryOperand.MINUS
                        if node.right.op == BinaryOperand.PLUS
                        else BinaryOperand.PLUS
                    )
                    node.replace(node.right)
            elif isinstance(node.right, UnOp):
                if node.right.op == UnaryOperand.MINUS:
                    node.replace(node.right.right)

    def visit_If(self, node: If) -> None:
        super().visit_If(node)
        if isinstance(node.test, Boolean):
            if node.test.value:
                node.replace(node.true)
            elif node.false:
                node.replace(node.false)
            else:
                node.remove()
