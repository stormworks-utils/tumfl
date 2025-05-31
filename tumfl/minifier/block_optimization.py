from tumfl.AST import Assign, Block, LocalAssign, Name
from tumfl.basic_walker import NoneWalker


class Optimize(NoneWalker):
    def visit_Block(self, node: Block) -> None:
        super().visit_Block(node)
        local_assigns: list[LocalAssign] = [
            stmt for stmt in node.statements if isinstance(stmt, LocalAssign)
        ]
        if len(local_assigns) > 1:
            new_assign = LocalAssign(local_assigns[0].token, [], [])
            for assign in local_assigns:
                new_assign.variable_names.extend(assign.variable_names)
            node.statements.insert(0, new_assign)
            for assign in local_assigns:
                if assign.expressions:
                    targets: list[Name] = [name.name for name in assign.variable_names]
                    normal_assign = Assign(assign.token, targets, assign.expressions)
                    assign.replace(normal_assign)
                else:
                    assign.remove()
