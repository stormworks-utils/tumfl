from __future__ import annotations

from pathlib import Path
from typing import Optional

from .AST import ASTNode, Chunk, FunctionCall, Name, Semicolon, String
from .basic_walker import NoneWalker
from .error import InvalidDependencyError
from .parser import parse
from .Token import Token, TokenType


def _parse_file(path: Path) -> Chunk:
    with path.open() as f:
        chunk: str = f.read()
    ast = parse(chunk)
    ast.parent(None, path)
    return ast


class ResolveDependencies(NoneWalker):
    def __init__(self, search_path: list[Path]):
        self.search_path: list[Path] = search_path
        self.found: dict[Path, Optional[list[Name]]] = {}

    @staticmethod
    def _str_to_name(name: str) -> Name:
        return Name.from_token(Token(TokenType.NAME, name, 0, 0))

    def _find_file_in_path(self, name: str, start_path: Path) -> Optional[Path]:
        parts: list[str] = name.split(".")
        if not parts[0]:
            return None
        filename: Path = Path(parts.pop(0))
        for file in parts:
            filename /= file
        for path in (start_path, *self.search_path):
            for suffix in ("", ".tl", ".lua"):
                current_path = path.joinpath(filename.with_suffix(suffix))
                if current_path.is_file():
                    return current_path
        return None

    def _parse_block_dependency(
        self, name: str, start_path: Path, token: Token
    ) -> Optional[Chunk]:
        path: Optional[Path] = self._find_file_in_path(name, start_path)
        if not path:
            raise InvalidDependencyError(
                f"Could not find dependency with name {name}", token
            )
        if path in self.found:
            return None
        self.found[path] = None
        return _parse_file(path)

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        if isinstance(node.function, Name) and node.function.variable_name == "require":
            if len(node.arguments) == 1 and isinstance(
                name := node.arguments[0], String
            ):
                assert isinstance(name, String)
                assert node.file_name
                ast: Optional[Chunk | Semicolon] = self._parse_block_dependency(
                    name.value, node.file_name.parent, node.token
                )
                if not ast:
                    ast = Semicolon(node.token)
                assert node.parent_class
                node.parent_class.replace_child(node, ast)
                ast.parent_class = node.parent_class
                self.visit(ast)
            else:
                raise InvalidDependencyError(
                    f"Wrong require() arguments. Expected single string, got {node.arguments}",
                    node.token,
                )
        else:
            super().visit_FunctionCall(node)


def resolve_recursive(path: Path, search_path: list[Path]) -> ASTNode:
    ast = _parse_file(path)
    resolver = ResolveDependencies(search_path)
    resolver.visit(ast)
    return ast
