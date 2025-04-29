from logging import warning

from .AST import ASTNode, String
from .basic_walker import NoneWalker


class Config(NoneWalker):
    def __init__(self, replacements: dict[str, ASTNode], prefix: str = "$$"):
        super().__init__()
        self.replacements: dict[str, ASTNode] = replacements
        self.prefix: str = prefix

    def visit_String(self, node: String) -> None:
        if node.value.startswith(self.prefix):
            if node.value[len(self.prefix) :] in self.replacements:
                node.replace(self.replacements[node.value[len(self.prefix) :]])
            else:
                warning(f"Found placeholder with no assigned value: {node.value}")
