from typing import Optional

from tumfl.AST import (
    ASTNode,
    BinaryOperand,
    BinOp,
    Block,
    Boolean,
    ExpFunctionCall,
    ExpFunctionDefinition,
    FunctionCall,
    FunctionDefinition,
    If,
    LocalFunctionDefinition,
    Number,
    Semicolon,
    UnaryOperand,
    UnOp,
)
from tumfl.basic_walker import AggregatingWalker, NoneWalker
from tumfl.minifier.shorten_names import Variable


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

    def handle_function(self, node: FunctionCall | ExpFunctionCall) -> None:
        var = node.get_attribute(Variable)
        if var and len(var.writes) == 1:
            definition: Optional[ASTNode] = var.writes[0].parent_class
            assert isinstance(
                definition,
                (FunctionDefinition, LocalFunctionDefinition, ExpFunctionDefinition),
            )
            if all(
                isinstance(child, Semicolon) for child in definition.body.statements
            ):
                node.remove()
            elif len(var.reads) == 1 and not self.has_return(definition.body):
                # inline function
                ...

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        super().visit_FunctionCall(node)
        self.handle_function(node)

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> None:
        super().visit_ExpFunctionCall(node)
        self.handle_function(node)
