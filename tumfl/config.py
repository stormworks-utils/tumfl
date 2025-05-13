from logging import warning
from pathlib import Path

from .AST import Assign, ASTNode, Name, String
from .basic_walker import NoneWalker
from .dependency_resolver import resolve_recursive


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


class ParameterGetter(NoneWalker):
    def __init__(self) -> None:
        super().__init__()
        self.parameters: dict[str, ASTNode] = {}

    def visit_Assign(self, node: Assign) -> None:
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], Name)
            and len(node.expressions) == 1
        ):
            name = node.targets[0]
            assert isinstance(name, Name)
            self.parameters[name.variable_name] = node.expressions[0]
        else:
            warning(f"Ignoring config parameter {node}")


def parse_config(file: Path) -> Config:
    chunk: ASTNode = resolve_recursive(file, [file.parent])
    getter = ParameterGetter()
    getter.visit(chunk)
    return Config(getter.parameters)
