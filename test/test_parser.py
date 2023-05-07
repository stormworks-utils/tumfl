import unittest

from tumfl.AST import *
from tumfl.lexer import Lexer
from tumfl.parser import Parser, ParserException
from tumfl.Token import Token, TokenType


class TestParser(unittest.TestCase):
    @staticmethod
    def parse_number(to_parse: str) -> Number:
        lex = Lexer(to_parse)
        return Number.from_token(lex.get_next_token())

    @staticmethod
    def parse_name(name: str) -> Name:
        return Name.from_token(Token(TokenType.NAME, name, 0, 0))

    @staticmethod
    def parse_string(string: str) -> String:
        return String.from_token(Token(TokenType.STRING, string, 0, 0))

    def test_simple_exp(self):
        parser = Parser("1+2")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            self.parse_number("1"),
            self.parse_number("2"),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(expected_tree, actual_tree)
        parser = Parser("4+5*6")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            self.parse_number("4"),
            BinOp.from_token(
                Token(TokenType.MULT, "*", 0, 0),
                self.parse_number("5"),
                self.parse_number("6"),
            ),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(expected_tree, actual_tree)
        parser = Parser("true and false or 1")
        expected_tree = BinOp.from_token(
            Token(TokenType.OR, "or", 0, 0),
            BinOp.from_token(
                Token(TokenType.AND, "and", 0, 0),
                Boolean.from_token(Token(TokenType.TRUE, "true", 0, 0)),
                Boolean.from_token(Token(TokenType.FALSE, "false", 0, 0)),
            ),
            self.parse_number("1"),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(expected_tree, actual_tree)
        parser = Parser("-nil")
        expected_tree = UnOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            Nil.from_token(Token(TokenType.NIL, "nil", 0, 0)),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, UnOp)
        self.assertEqual(expected_tree, actual_tree)
        parser = Parser("#'a'")
        expected_tree = UnOp.from_token(
            Token(TokenType.HASH, "#", 0, 0),
            self.parse_string("a"),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, UnOp)
        self.assertEqual(expected_tree, actual_tree)

    def test_associativity(self):
        parser = Parser("1^2^3")
        expected_tree = BinOp.from_token(
            Token(TokenType.EXPONENT, "^", 0, 0),
            self.parse_number("1"),
            BinOp.from_token(
                Token(TokenType.EXPONENT, "^", 0, 0),
                self.parse_number("2"),
                self.parse_number("3"),
            ),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(expected_tree, actual_tree)
        parser = Parser("1+2-3")
        expected_tree = BinOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            BinOp.from_token(
                Token(TokenType.PLUS, "+", 0, 0),
                self.parse_number("1"),
                self.parse_number("2"),
            ),
            self.parse_number("3"),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(expected_tree, actual_tree)

    def test_error(self):
        parser = Parser("1+")
        with self.assertRaises(ParserException):
            parser._parse_exp()

    def test_unary_expr(self):
        parser = Parser("1- -2")
        expected_tree = BinOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            self.parse_number("1"),
            UnOp.from_token(Token(TokenType.MINUS, "-", 0, 0), self.parse_number("2")),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(actual_tree, expected_tree)

    def test_len_operator(self):
        parser = Parser("#a + 1")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            UnOp.from_token(
                Token(TokenType.HASH, "#", 0, 0),
                self.parse_name("a"),
            ),
            self.parse_number("1"),
        )
        actual_tree = parser._parse_exp()
        self.assertIsInstance(actual_tree, BinOp)
        self.assertEqual(actual_tree, expected_tree)

    def test_wrong_token(self):
        parser = Parser("a,b+")
        with self.assertRaises(ParserException):
            parser.parse_chunk()
        parser = Parser("a=1\nb,c+")
        with self.assertRaises(ParserException):
            parser.parse_chunk()

    def test_parse_var(self):
        parser = Parser('a["b"].d')
        expected_tree = NamedIndex(
            Token(TokenType.NAME, "d", 0, 0),
            Index(
                Token(TokenType.R_BRACKET, "[", 0, 0),
                self.parse_name("a"),
                self.parse_string("b"),
            ),
            self.parse_name("d"),
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        parser = Parser("(2)[1]")
        expected_tree = Index(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            self.parse_number("1"),
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        parser = Parser("(2)(1)")
        expected_tree = ExpFunctionCall(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            [self.parse_number("1")],
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        parser = Parser("a:b()")
        expected_tree = ExpMethodInvocation(
            Token(TokenType.COLON, "[", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
            [],
        )
        self.assertEqual(parser._parse_var(), expected_tree)

    def test_table_constructor(self):
        parser = Parser("{}")
        expected_result = Table(Token(TokenType.L_CURL, "{", 0, 0), [])
        self.assertEqual(parser._parse_table_constructor(), expected_result)
        parser = Parser("{a}")
        expected_result = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NumberedTableField(
                    Token(TokenType.NAME, "a", 0, 0), self.parse_name("a")
                )
            ],
        )
        self.assertEqual(parser._parse_table_constructor(), expected_result)
        parser = Parser('{["b"]=c}')
        expected_result = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                ExplicitTableField(
                    Token(TokenType.L_BRACKET, "[", 0, 0),
                    self.parse_string("b"),
                    self.parse_name("c"),
                )
            ],
        )
        self.assertEqual(parser._parse_table_constructor(), expected_result)
        parser = Parser("{a=b}")
        expected_result = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NamedTableField(
                    Token(TokenType.NAME, "a", 0, 0),
                    self.parse_name("a"),
                    self.parse_name("b"),
                )
            ],
        )
        self.assertEqual(parser._parse_table_constructor(), expected_result)
        parser = Parser("{a, b,}")
        expected_result = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NumberedTableField(
                    Token(TokenType.NAME, "a", 0, 0), self.parse_name("a")
                ),
                NumberedTableField(
                    Token(TokenType.NAME, "b", 0, 0), self.parse_name("b")
                ),
            ],
        )
        self.assertEqual(parser._parse_table_constructor(), expected_result)

    def test_parse_args(self):
        parser = Parser("()")
        self.assertEqual(parser._parse_args(), [])
        parser = Parser('(a, b, "d", 1)')
        expected_args = [
            self.parse_name("a"),
            self.parse_name("b"),
            self.parse_string("d"),
            self.parse_number("1"),
        ]
        self.assertEqual(parser._parse_args(), expected_args)
        parser = Parser("(a,b")
        with self.assertRaises(ParserException):
            parser._parse_args()
        parser = Parser("(a,b,)")
        with self.assertRaises(ParserException):
            parser._parse_args()
        parser = Parser('"abc"')
        self.assertEqual(parser._parse_args(), [self.parse_string("abc")])
        parser = Parser('{a,"b"}')
        table_result = parser._parse_table_constructor()
        parser = Parser('{a,"b"}')
        self.assertEqual(parser._parse_args(), [table_result])

    def test_parse_names(self):
        parser = Parser("a b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        parser = Parser("a, b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        parser = Parser("b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        parser = Parser(",b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        parser = Parser("a,")
        with self.assertRaises(ParserException):
            parser._parse_name_list()
        parser = Parser("a, 1")
        with self.assertRaises(ParserException):
            parser._parse_name_list()

    def test_assign(self):
        parser = Parser('a = "bcd"')
        expected_tree = Chunk(
            Token(TokenType.NAME, "a", 0, 0),
            [
                Assign(
                    Token(TokenType.NAME, "a", 0, 0),
                    [self.parse_name("a")],
                    [self.parse_string("bcd")],
                )
            ],
            [],
        )
        actual_tree = parser.parse_chunk()
        self.assertEqual(actual_tree, expected_tree)
        parser = Parser('a,b,c = "bcd"')
        expected_tree = Chunk(
            Token(TokenType.NAME, "a", 0, 0),
            [
                Assign(
                    Token(TokenType.NAME, "a", 0, 0),
                    [
                        self.parse_name("a"),
                        self.parse_name("b"),
                        self.parse_name("c"),
                    ],
                    [self.parse_string("bcd")],
                )
            ],
            [],
        )
        actual_tree = parser.parse_chunk()
        self.assertEqual(actual_tree, expected_tree)
        parser = Parser('a = "bcd", "def"')
        expected_tree = Chunk(
            Token(TokenType.NAME, "a", 0, 0),
            [
                Assign(
                    Token(TokenType.NAME, "a", 0, 0),
                    [self.parse_name("a")],
                    [
                        self.parse_string("bcd"),
                        self.parse_string("def"),
                    ],
                )
            ],
            [],
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
