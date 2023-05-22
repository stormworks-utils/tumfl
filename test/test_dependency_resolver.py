import unittest
from pathlib import Path

from tumfl.dependency_resolver import (
    Chunk,
    FunctionCall,
    InvalidDependencyError,
    Semicolon,
    resolve_recursive,
)


class TestDependencyResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.base_path: Path = Path(__file__).parent / "test_files"
        self.main_script: Path = self.base_path / "main.lua"
        assert self.main_script.is_file()

    def test_resolver(self) -> None:
        ast = resolve_recursive(self.main_script, [self.base_path])
        assert isinstance(ast, Chunk)
        self.assertIsInstance(ast.statements[0], Chunk)
        self.assertIsInstance(ast.statements[1], Chunk)
        self.assertIsInstance(ast.statements[2], Semicolon)
        self.assertIsInstance(ast.statements[3], FunctionCall)

    def test_errors(self) -> None:
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(self.base_path / "empty_path.lua", [self.base_path])
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(self.base_path / "nonexistent_path.lua", [self.base_path])
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(self.base_path / "dual_path.lua", [self.base_path])
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(self.base_path / "number_path.lua", [self.base_path])
