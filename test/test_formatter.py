import unittest

from tumfl.AST import Block, If
from tumfl.formatter import Formatter, FormattingStyle, MinifiedStyle, Separators
from tumfl.parser import Parser


class TestFormatter(unittest.TestCase):
    def setUp(self) -> None:
        self.normal: Formatter = Formatter(FormattingStyle)
        self.minified: Formatter = Formatter(MinifiedStyle)

    def test_format_comment(self):
        expected = ["-- comment", Separators.Newline]
        self.assertEqual(self.normal._format_comment("comment"), expected)
        expected = ["--comment", Separators.Newline]
        self.assertEqual(self.minified._format_comment("comment"), expected)
        expected = ["--[[ab\ncd]]", Separators.Statement]
        self.assertEqual(self.normal._format_comment("ab\ncd"), expected)
        expected = ["--[==[[[=[\na]==]", Separators.Statement]
        self.assertEqual(self.normal._format_comment("[[=[\na"), expected)

    def test_format_function_args(self):
        parser = Parser("'abc'{}1'ghi','jkl'")
        expression = parser._parse_exp()  # "abc"
        expected = ["(", *self.normal.visit(expression), ")"]
        self.assertEqual(self.normal._format_function_args([expression]), expected)
        expected = self.normal.visit(expression)
        self.assertEqual(self.minified._format_function_args([expression]), expected)
        expression = parser._parse_exp()  # {}
        expected = ["(", *self.normal.visit(expression), ")"]
        self.assertEqual(self.normal._format_function_args([expression]), expected)
        expected = self.normal.visit(expression)
        self.assertEqual(self.minified._format_function_args([expression]), expected)
        expression = parser._parse_exp()  # 1
        expected = ["(", *self.normal.visit(expression), ")"]
        self.assertEqual(self.minified._format_function_args([expression]), expected)
        expression = parser._parse_exp_list()  # "ghi", "jkl"
        expected = [
            "(",
            *self.normal.visit(expression[0]),
            Separators.Argument,
            *self.normal.visit(expression[1]),
            ")",
        ]
        self.assertEqual(self.normal._format_function_args(expression), expected)
        self.assertEqual(self.minified._format_function_args(expression), expected)

    def test_Assign(self):
        stmt = Parser("a = b")._parse_statement()
        expected = ["a", Separators.Space, "=", Separators.Space, "b"]
        self.assertEqual(self.normal.visit(stmt), expected)
        self.assertEqual(self.minified.visit(stmt), expected)

    def test_block(self):
        chunk = Parser("--comment\na=b c=d return a").parse_chunk()
        expected = [
            Separators.DeIndent,
            Separators.Indent,
            "-- comment",
            Separators.Newline,
            *self.normal.visit(chunk.statements[0]),
            Separators.Statement,
            *self.normal.visit(chunk.statements[1]),
            Separators.Statement,
            "return",
            Separators.Space,
            "a",
        ]
        self.assertEqual(self.normal.visit(chunk), expected)
        expected.pop(2)
        expected.pop(2)
        self.assertEqual(self.minified.visit(chunk), expected)
        chunk = Parser("a=b").parse_chunk()
        expected = [
            Separators.DeIndent,
            Separators.Indent,
            *self.normal.visit(chunk.statements[0]),
        ]
        self.assertEqual(self.normal.visit(chunk), expected)

    def test_Boolean(self):
        parser = Parser("true false")
        expr = parser._parse_exp()
        expected = ["true"]
        self.assertEqual(self.normal.visit(expr), expected)
        self.assertEqual(self.minified.visit(expr), expected)
        expr = parser._parse_exp()
        expected = ["false"]
        self.assertEqual(self.normal.visit(expr), expected)
        self.assertEqual(self.minified.visit(expr), expected)

    def test_Break(self):
        expr = Parser("break")._parse_break()
        expected = ["break"]
        self.assertEqual(self.normal.visit(expr), expected)

    def test_Goto(self):
        stmt = Parser("goto label")._parse_statement()
        expected = ["goto", Separators.Space, "label"]
        self.assertEqual(self.normal.visit(stmt), expected)

    def test_If(self):
        stmt = Parser("if 1 then a=b elseif 0 then c=d else e=f end")._parse_if()
        assert isinstance(stmt.false, If)
        assert isinstance(stmt.false.false, Block)
        expected = [
            "if",
            Separators.Space,
            "1",
            Separators.Space,
            "then",
            Separators.Statement,
            *self.normal.visit(stmt.true),
            "elseif",
            Separators.Space,
            "0",
            Separators.Space,
            "then",
            Separators.Statement,
            *self.normal.visit(stmt.false.true),
            "else",
            Separators.Statement,
            *self.normal.visit(stmt.false.false),
            "end",
        ]
        self.assertEqual(self.normal.visit(stmt), expected)
        stmt = Parser("if 1 then a=b end")._parse_if()
        expected = [
            "if",
            Separators.Space,
            "1",
            Separators.Space,
            "then",
            Separators.Statement,
            *self.normal.visit(stmt.true),
            "end",
        ]
        self.assertEqual(self.normal.visit(stmt), expected)
