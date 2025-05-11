from tumfl.AST import Block, LocalAssign
from tumfl.basic_walker import NoneWalker


class CombineLocal(NoneWalker):
    def visit_Block(self, node: Block) -> None:
        for i in range(len(node.statements) - 1, 0, -1):
            if isinstance(node.statements[i], LocalAssign) and isinstance(
                node.statements[i - 1], LocalAssign
            ):
                to_remove = node.statements[i]
                assert isinstance(to_remove, LocalAssign)
                move_into = node.statements[i - 1]
                assert isinstance(move_into, LocalAssign)
                if (
                    to_remove.expressions is not None
                    and move_into.expressions is not None
                ):
                    move_into.variable_names.extend(to_remove.variable_names)
                    move_into.expressions.extend(to_remove.expressions)
                    node.statements.pop(i)
        super().visit_Block(node)
