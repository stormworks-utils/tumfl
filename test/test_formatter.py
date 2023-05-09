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

    def test_Index(self):
        index = Parser("a[1]")._parse_var()
        expected = ["a", "[", "1", "]"]
        self.assertEqual(self.normal.visit(index), expected)

    def test_Label(self):
        stmt = Parser("::label::")._parse_statement()
        expected = ["::", "label", "::"]
        self.assertEqual(self.normal.visit(stmt), expected)

    def test_Name(self):
        name = Parser("abc")._parse_var()
        expected = ["abc"]
        self.assertEqual(self.normal.visit(name), expected)

    def test_Nil(self):
        exp = Parser("nil")._parse_exp()
        expected = ["nil"]
        self.assertEqual(self.normal.visit(exp), expected)

    def test_Number(self):
        exp = Parser("1.23")._parse_exp()
        expected = ["1.23"]
        self.assertEqual(self.normal.visit(exp), expected)

    def test_Repeat(self):
        stmt = Parser("repeat a=b until 1")._parse_repeat()
        expected = [
            "repeat",
            Separators.Statement,
            *self.normal.visit(stmt.body),
            "until",
            Separators.Space,
            "1",
        ]
        self.assertEqual(self.normal.visit(stmt), expected)

    def test_Semicolon(self):
        stmt = Parser(";")._parse_statement()
        expected = [";"]
        self.assertEqual(self.normal.visit(stmt), expected)

    def test_String(self):
        parser = Parser("'abc''def\"'[[ghi\njkl]][[mno'\"\"]][===[[[=[==[\n]===]")
        exp = parser._parse_exp()
        expected = ['"abc"']
        self.assertEqual(self.normal.visit(exp), expected)
        self.assertEqual(self.minified.visit(exp), expected)
        exp = parser._parse_exp()
        expected = ['"def\\""']
        self.assertEqual(self.normal.visit(exp), expected)
        expected = ["'def\"'"]
        self.assertEqual(self.minified.visit(exp), expected)
        exp = parser._parse_exp()
        expected = ["[[ghi\njkl]]"]
        self.assertEqual(self.normal.visit(exp), expected)
        self.assertEqual(self.minified.visit(exp), expected)
        exp = parser._parse_exp()
        expected = ['"mno\'\\"\\""']
        self.assertEqual(self.normal.visit(exp), expected)
        expected = ["'mno\\'\"\"'"]
        self.assertEqual(self.minified.visit(exp), expected)
        exp = parser._parse_exp()
        expected = ["[===[[[=[==[\n]===]"]
        self.assertEqual(self.normal.visit(exp), expected)
        self.assertEqual(self.minified.visit(exp), expected)

    def test_Table(self):
        table = Parser("{a,b}")._parse_table_constructor()
        expected = ["{", "a", Separators.Argument, "b", "}"]
        self.assertEqual(self.normal.visit(table), expected)

    def test_Vararg(self):
        exp = Parser("...")._parse_exp()
        expected = ["..."]
        self.assertEqual(self.normal.visit(exp), expected)

    def test_While(self):
        stmt = Parser("while i do a=b end")._parse_while()
        expected = [
            "while",
            Separators.Space,
            "i",
            Separators.Space,
            "do",
            Separators.Statement,
            *self.normal.visit(stmt.body),
            "end",
        ]
        self.assertEqual(self.normal.visit(stmt), expected)

    def test_Field(self):
        index = Parser("[1]=2")._parse_field()
        expected = ["[", "1", "]", Separators.Space, "=", Separators.Space, "2"]
        self.assertEqual(self.normal.visit(index), expected)
