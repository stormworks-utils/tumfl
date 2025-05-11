from typing import Optional

from tumfl.AST import BinaryOperand, BinOp, Number, UnaryOperand, UnOp
from tumfl.basic_walker import NoneWalker


class Simplify(NoneWalker):
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
