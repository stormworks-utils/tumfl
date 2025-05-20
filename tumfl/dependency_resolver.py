from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .AST import (
    ASTNode,
    Block,
    Chunk,
    ExpFunctionCall,
    ExpFunctionDefinition,
    FunctionCall,
    Name,
    NumberedTableField,
    Semicolon,
    String,
    Table,
)
from .basic_walker import NoneWalker
from .error import InvalidDependencyError
from .parser import parse
from .Token import Token

if TYPE_CHECKING:
    from .config import Config


def _parse_file(path: Path, config: Optional[Config]) -> Chunk:
    with path.open() as f:
        chunk: str = f.read()
    ast: Chunk = parse(chunk)
    ast.parent(None, path)
    if config:
        config.visit(ast)
    return ast


class ResolveDependencies(NoneWalker):
    def __init__(
        self,
        search_path: list[Path],
        add_source_description: bool = False,
        config: Optional[Config] = None,
    ):
        self.search_path: list[Path] = search_path
        self.found: dict[Path, Optional[list[Name]]] = {}
        self.add_source_description: bool = add_source_description
        self.config: Optional[Config] = config

    def _find_file_in_path(self, name: str, start_path: Path) -> Optional[Path]:
        parts: list[str] = name.split(".")
        if not parts[0]:
            return None
        filename: Path = Path(parts[0])
        for file in parts[1:]:
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

    def __find_and_parse(
        self, name: str, node: ASTNode, deduplicate: bool, results: list[Chunk]
    ) -> None:
        assert node.file_name
        name = name.replace("/", ".")
        dependency_path: Optional[Path] = self._get_block_dependency_path(
            name, node.file_name.parent, node.token, deduplicate
        )
        if dependency_path:
            ast: Chunk = _parse_file(dependency_path, self.config)
            if self.add_source_description:
                ast.comment.insert(0, f"Sourced from {dependency_path}")
            results.append(ast)

    def __get_table_dependencies(
        self, node: Table, results: list[Chunk], deduplicate: bool
    ) -> None:
        for item in node.fields:
            if isinstance(item, NumberedTableField):
                if isinstance(item.value, String):
                    self.__find_and_parse(item.value.value, node, deduplicate, results)
                else:
                    raise InvalidDependencyError(
                        f"Wrong require() arguments. Table can only contain strings, got {item}",
                        node.token,
                    )
            else:
                raise InvalidDependencyError(
                    f"Wrong require() arguments. Can only use strings with no explicit index, got {item}",
                    node.token,
                )

    def __get_ast(
        self, node: Union[FunctionCall, ExpFunctionCall], deduplicate: bool = True
    ) -> Optional[Chunk | Semicolon | Block]:
        if isinstance(node.function, Name) and node.function.variable_name == "require":
            results: list[Chunk] = []
            for arg in node.arguments:
                if isinstance(arg, String):
                    self.__find_and_parse(arg.value, node, deduplicate, results)
                elif isinstance(arg, Table):
                    self.__get_table_dependencies(arg, results, deduplicate)
                else:
                    raise InvalidDependencyError(
                        f"Wrong require() arguments. Expected string or table, got {arg}",
                        node.token,
                    )
            ast: Union[Chunk, Semicolon, Block]
            if not results:
                ast = Semicolon(node.token)
                ast.parent(node.parent_class, node.file_name)
            elif len(results) == 1:
                ast = results[0]
            else:
                ast = Block(node.token, results, None)
            return ast
        return None

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        if ast := self.__get_ast(node):
            if isinstance(ast, Semicolon):
                assert node.parent_class
                node.remove()
            else:
                ast.parent_class = node.parent_class
                node.replace(ast)
                self.visit(ast)
        else:
            super().visit_FunctionCall(node)

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> None:
        # if the body is expecting a return value, never deduplicate
        if ast := self.__get_ast(node, deduplicate=False):
            # since deduplication is off, ast will never be a Semicolon
            assert isinstance(ast, Block)
            function = ExpFunctionDefinition(node.token, [], ast)
            node.function = function
            ast.parent_class = function
            call = ExpFunctionCall(node.token, function, [])
            function.parent_class = call
            call.parent_class = node.parent_class
            ast.file_name = function.file_name = call.file_name = node.file_name
            node.replace(call)
            self.visit(call)
        else:
            super().visit_ExpFunctionCall(node)


def resolve_recursive(
    path: Path,
    search_path: list[Path],
    add_source_description: bool = False,
    config: Optional[Config] = None,
) -> ASTNode:
    ast = _parse_file(path, config)
    resolver = ResolveDependencies(search_path, add_source_description, config=config)
    resolver.visit(ast)
    return ast
