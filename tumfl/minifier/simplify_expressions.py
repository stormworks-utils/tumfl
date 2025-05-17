from __future__ import annotations

from logging import warning
from typing import Optional

from tumfl.AST import (
    ASTNode,
    BinaryOperand,
    BinOp,
    Block,
    Boolean,
    ExpFunctionDefinition,
    ExpMethodInvocation,
    FunctionCall,
    FunctionDefinition,
    If,
    LocalFunctionDefinition,
    MethodInvocation,
    Name,
    NamedIndex,
    NamedTableField,
    Number,
    Semicolon,
    UnaryOperand,
    UnOp,
)
from tumfl.basic_walker import AggregatingWalker, NoneWalker

from .util.remove_name import RemoveName
from .util.variable import Variable


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
            elif isinstance(parent, NamedTableField) and node is not parent.value:
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

    def visit_BinOp(self, node: BinOp) -> None:
        super().visit_BinOp(node)
        if isinstance(node.left, Number) and isinstance(node.right, Number):
            left_num: str = str(node.left.to_int() or node.left.to_float())
            right_num: str = str(node.right.to_int() or node.right.to_float())
            op: str = node.op.value.replace("^", "**").replace("~=", "!=")
            # pylint: disable=eval-used
            result = str(eval(f"{left_num} {op} {right_num}"))
            new_node = Number(node.token, False, result.split(".", maxsplit=1)[0])
            if "." in result:
                new_node.fractional_part = result.split(".")[1]
            node.replace(new_node)

    def visit_UnOp(self, node: UnOp) -> None:
        super().visit_UnOp(node)
        if node.op == UnaryOperand.NOT:
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
            if isinstance(node.right, Number):
                if not node.right.integer_part:
                    node.right.integer_part = "-"
                elif node.right.integer_part.startswith("-"):
                    node.right.integer_part = node.right.integer_part[1:]
                else:
                    node.right.integer_part = "-" + node.right.integer_part
                node.replace(node.right)
            elif isinstance(node.right, BinOp):
                if node.right.op in (BinaryOperand.PLUS, BinaryOperand.MINUS):
                    node.right.op = (
                        BinaryOperand.MINUS
                        if node.right.op == BinaryOperand.PLUS
                        else BinaryOperand.PLUS
                    )
                    node.replace(node.right)

    def visit_If(self, node: If) -> None:
        super().visit_If(node)
        if isinstance(node.test, Boolean):
            if node.test.value:
                node.replace(node.true)
            elif node.false:
                node.replace(node.false)

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        super().visit_FunctionCall(node)
        var = node.get_attribute(Variable)
        if var and len(var.writes) == 1:
            definition: Optional[ASTNode] = var.writes[0].parent_class
            if not isinstance(
                definition,
                (FunctionDefinition, LocalFunctionDefinition, ExpFunctionDefinition),
            ):
                warning(
                    f'Function call to "{node.function!s}" is not a function definition'
                )
                return
            if (
                all(
                    isinstance(child, Semicolon) for child in definition.body.statements
                )
                and not definition.body.returns
            ):
                self.remove_name(node)
                node.remove()
                if len(var.reads) == 0:
                    definition.remove()
            elif (
                len(var.reads) == 1
                and all(isinstance(arg, Name) for arg in node.arguments)
                and all(isinstance(arg, Name) for arg in definition.parameters)
                and not self.has_return(definition.body)
            ):
                # Inlining is quite conservative, inlining only functions that have only name arguments,
                # and no return statements (and for obvious reasons, only if there is only 1 callee)
                replacements: dict[Name, Name] = {}
                for arg, value in zip(definition.parameters, node.arguments):
                    assert isinstance(arg, Name) and isinstance(value, Name)
                    replacements[arg] = value
                ReplaceName(replacements).visit(definition.body)
                node.replace(definition.body)
                definition.remove()
