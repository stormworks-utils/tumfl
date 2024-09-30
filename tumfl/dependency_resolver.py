from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from .AST import (
    ASTNode,
    Chunk,
    ExpFunctionCall,
    ExpFunctionDefinition,
    FunctionCall,
    Name,
    Semicolon,
    String,
)
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
    def __init__(self, search_path: list[Path], add_source_description: bool = False):
        self.search_path: list[Path] = search_path
        self.found: dict[Path, Optional[list[Name]]] = {}
        self.add_source_description: bool = add_source_description

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

    def _get_block_dependency_path(
        self, name: str, start_path: Path, token: Token, deduplicate: bool = True
    ) -> Optional[Path]:
        path: Optional[Path] = self._find_file_in_path(name, start_path)
        if not path:
            raise InvalidDependencyError(
                f"Could not find dependency with name {name}", token
            )
        if deduplicate and path in self.found:
            return None
        self.found[path] = None
        return path

    def __get_ast(
        self, node: Union[FunctionCall, ExpFunctionCall], deduplicate: bool = True
    ) -> Optional[Chunk | Semicolon]:
        if isinstance(node.function, Name) and node.function.variable_name == "require":
            if len(node.arguments) == 1 and isinstance(
                name := node.arguments[0], String
            ):
                assert isinstance(name, String)
                assert node.file_name
                dependency_path: Optional[Path] = self._get_block_dependency_path(
                    name.value, node.file_name.parent, node.token, deduplicate
                )
                assert node.parent_class
                ast: Union[Chunk | Semicolon]
                if dependency_path:
                    ast = _parse_file(dependency_path)
                    if self.add_source_description:
                        ast.comment.insert(0, f"Sourced from {dependency_path}")
                else:
                    ast = Semicolon(node.token)
                    ast.parent(node.parent_class, node.file_name)
                return ast
            raise InvalidDependencyError(
                f"Wrong require() arguments. Expected single string, got {node.arguments}",
                node.token,
            )
        return None

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        if ast := self.__get_ast(node):
            assert node.parent_class
            node.parent_class.replace_child(node, ast)
            ast.parent_class = node.parent_class
            self.visit(ast)
        else:
            super().visit_FunctionCall(node)

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> None:
        # if the body is expecting a return value, never deduplicate
        if ast := self.__get_ast(node, deduplicate=False):
            # since deduplication is off, ast will never be a Semicolon
            assert isinstance(ast, Chunk)
            function = ExpFunctionDefinition(node.token, [], ast)
            node.function = function
            ast.parent_class = function
            ast.file_name = node.file_name
            function.parent_class = node
            self.visit(function)
        else:
            super().visit_ExpFunctionCall(node)


def resolve_recursive(
    path: Path, search_path: list[Path], add_source_description: bool = False
) -> ASTNode:
    ast = _parse_file(path)
    resolver = ResolveDependencies(search_path, add_source_description)
    resolver.visit(ast)
    return ast
