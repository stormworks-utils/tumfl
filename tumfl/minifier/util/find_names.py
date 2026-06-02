from tumfl.AST import Name
from tumfl.basic_walker import NoneWalker


class FindNames(NoneWalker):
    def __init__(self) -> None:
        super().__init__()
        self.names: set[str] = set()

    def visit_Name(self, node: Name) -> None:
        self.names.add(node.variable_name)
