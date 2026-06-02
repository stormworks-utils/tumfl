from tumfl.AST import Assign, Block, LocalAssign, Name
from tumfl.basic_walker import NoneWalker
from tumfl.minifier.util.find_names import FindNames


class Optimize(NoneWalker):
    def visit_Block(self, node: Block) -> None:
        super().visit_Block(node)
        local_assigns: list[LocalAssign] = []
        local_names: set[Name] = set()
        global_names: set[str] = set()
        for stmt in node.statements:
            if isinstance(stmt, LocalAssign):
                local_assigns.append(stmt)
                local_names.update(name.name for name in stmt.variable_names)
                references = FindNames()
                for expression in stmt.expressions:
                    references.visit(expression)
                global_names.update(references.names)
            else:
                references = FindNames()
                references.visit(stmt)
                global_names.update(references.names)
        local_names_str: set[str] = {name.variable_name for name in local_names}
        if len(local_names) > 1 and not local_names_str.intersection(global_names):
            new_assign = LocalAssign(local_assigns[0].token, [], [])
            for assign in local_assigns:
                new_assign.variable_names.extend(assign.variable_names)
            node.statements.insert(0, new_assign)
            for assign in local_assigns:
                if assign.expressions:
                    normal_assign = Assign(assign.token, list(local_names), assign.expressions)
                    assign.replace(normal_assign)
                else:
                    assign.remove()
