from tumfl.AST import Assign, ASTNode, Block, LocalAssign, Name
from tumfl.basic_walker import NoneWalker
from tumfl.minifier.util.find_names import FindNames


class Optimize(NoneWalker):
    def __add_global_names(
        self, node: ASTNode, local_names: set[str], global_names: set[str]
    ) -> None:
        references = FindNames()
        references.visit(node)
        for reference in references.names:
            if reference not in local_names:
                global_names.add(reference)

    def visit_Block(self, node: Block) -> None:
        super().visit_Block(node)
        local_assigns: list[LocalAssign] = []
        local_names: set[str] = set()
        global_names: set[str] = set()
        for stmt in node.statements:
            if isinstance(stmt, LocalAssign):
                if stmt.expressions:
                    for expression in stmt.expressions:
                        self.__add_global_names(expression, local_names, global_names)
                local_assigns.append(stmt)
                local_names.update(
                    name.name.variable_name for name in stmt.variable_names
                )
            else:
                self.__add_global_names(stmt, local_names, global_names)
        if len(local_names) > 1 and not local_names.intersection(global_names):
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
