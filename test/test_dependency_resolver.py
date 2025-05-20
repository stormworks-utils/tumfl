import unittest
from pathlib import Path

from tumfl.AST import (
    Assign,
    Block,
    ExpFunctionCall,
    ExpFunctionDefinition,
    Number,
    Semicolon,
    String,
)
from tumfl.config import parse_config
from tumfl.dependency_resolver import (
    Chunk,
    FunctionCall,
    InvalidDependencyError,
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
        self.assertEqual(len(ast.statements), 4)
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
            resolve_recursive(self.base_path / "number_path.lua", [self.base_path])

    def test_config(self):
        config = parse_config(self.base_path / "config.lua")

        ast = resolve_recursive(
            self.base_path / "config_test.lua", [self.base_path], config=config
        )
        assert isinstance(ast, Chunk)
        self.assertEqual(len(ast.statements), 1)
        assign = ast.statements[0]
        self.assertIsInstance(assign, Assign)
        assert isinstance(assign, Assign)
        self.assertEqual(len(assign.expressions), 2)
        first_value = assign.expressions[0]
        assert isinstance(first_value, String)
        self.assertEqual(first_value.value, "foo")
        second_value = assign.expressions[1]
        assert isinstance(second_value, Number)
        self.assertEqual(second_value.to_int(), 42)

    def test_add_source_description(self):
        ast = resolve_recursive(
            self.main_script, [self.base_path], add_source_description=True
        )
        assert isinstance(ast, Chunk)
        first_statement = ast.statements[0]
        self.assertEqual(len(first_statement.comment), 1)
        self.assertIn(
            "Sourced from",
            first_statement.comment[0],
        )
        self.assertIn(
            str(self.base_path / "a.lua"),
            first_statement.comment[0],
        )

    def test_multi_import(self):
        ast = resolve_recursive(self.base_path / "multi_import.lua", [self.base_path])
        assert isinstance(ast, Chunk)
        self.assertEqual(len(ast.statements), 1)
        first_statement = ast.statements[0]
        self.assertIsInstance(first_statement, Block)

    def test_invalid_path(self):
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(
                self.base_path / "invalid_require_path.lua", [self.base_path]
            )
        with self.assertRaises(InvalidDependencyError):
            resolve_recursive(
                self.base_path / "invalid_require_type.lua", [self.base_path]
            )

    def test_require_expr(self):
        ast = resolve_recursive(self.base_path / "require_expr.lua", [self.base_path])
        assert isinstance(ast, Chunk)
        self.assertEqual(len(ast.statements), 1)
        first_statement = ast.statements[0]
        self.assertIsInstance(first_statement, Assign)
        assert isinstance(first_statement, Assign)
        expression = first_statement.expressions[0]
        self.assertIsInstance(expression, ExpFunctionCall)
        assert isinstance(expression, ExpFunctionCall)
        self.assertEqual(len(expression.arguments), 0)
        func_def = expression.function
        self.assertIsInstance(func_def, ExpFunctionDefinition)
        assert isinstance(func_def, ExpFunctionDefinition)
        self.assertEqual(len(func_def.parameters), 0)
        self.assertEqual(len(func_def.body.statements), 0)
        assert func_def.body.returns is not None
        self.assertEqual(len(func_def.body.returns), 1)
