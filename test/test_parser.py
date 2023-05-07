import unittest

from tumfl.AST import *
from tumfl.AST.BaseFunctionDefinition import BaseFunctionDefinition
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

    @staticmethod
    def get_chunk(*statements: Statement) -> Chunk:
        return Chunk(statements[0].token, list(statements), [])

    def test_simple_exp(self):
        parser = Parser("1+2")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            self.parse_number("1"),
            self.parse_number("2"),
        )
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("-nil")
        expected_tree = UnOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            Nil.from_token(Token(TokenType.NIL, "nil", 0, 0)),
        )
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("#'a'")
        expected_tree = UnOp.from_token(
            Token(TokenType.HASH, "#", 0, 0),
            self.parse_string("a"),
        )
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

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
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

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
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(2)[1]")
        expected_tree = Index(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            self.parse_number("1"),
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(2)(1)")
        expected_tree = ExpFunctionCall(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            [self.parse_number("1")],
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("a:b()")
        expected_tree = ExpMethodInvocation(
            Token(TokenType.COLON, "[", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
            [],
        )
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

    def test_table_constructor(self):
        parser = Parser("{}")
        expected_result = Table(Token(TokenType.L_CURL, "{", 0, 0), [])
        self.assertEqual(parser._parse_table_constructor(), expected_result)
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(len(parser.context_hints), 0)
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
        self.assertEqual(len(parser.context_hints), 0)

    def test_parse_args(self):
        parser = Parser("()")
        self.assertEqual(parser._parse_args(), [])
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser('(a, b, "d", 1)')
        expected_args = [
            self.parse_name("a"),
            self.parse_name("b"),
            self.parse_string("d"),
            self.parse_number("1"),
        ]
        self.assertEqual(parser._parse_args(), expected_args)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(a,b")
        with self.assertRaises(ParserException):
            parser._parse_args()
        parser = Parser("(a,b,)")
        with self.assertRaises(ParserException):
            parser._parse_args()
        parser = Parser('"abc"')
        self.assertEqual(parser._parse_args(), [self.parse_string("abc")])
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser('{a,"b"}')
        table_result = parser._parse_table_constructor()
        parser = Parser('{a,"b"}')
        self.assertEqual(parser._parse_args(), [table_result])
        self.assertEqual(len(parser.context_hints), 0)

    def test_parse_names(self):
        parser = Parser("a b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("a, b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser(",b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("a,")
        with self.assertRaises(ParserException):
            parser._parse_name_list()
        parser = Parser("a, 1")
        with self.assertRaises(ParserException):
            parser._parse_name_list()

    def test_parse_vararg(self):
        parser = Parser("...")
        expected = Vararg(Token(TokenType.ELLIPSIS, "...", 0, 0))
        self.assertEqual(parser._parse_exp(), expected)
        self.assertEqual(len(parser.context_hints), 0)

    def test_parse_table_expr(self):
        parser = Parser("{a}")
        expected = Parser("{a}")._parse_table_constructor()
        self.assertEqual(parser._parse_exp(), expected)
        self.assertEqual(len(parser.context_hints), 0)

    def test_parse_funcbody(self):
        function_token = Token(TokenType.FUNCTION, "function", 0, 0)
        parser = Parser("()end")
        expected = BaseFunctionDefinition(
            function_token, [], Block(Token(TokenType.END, "end", 0, 0), [], [])
        )
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(a,b)end")
        expected = BaseFunctionDefinition(
            function_token,
            [self.parse_name("a"), self.parse_name("b")],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(...)end")
        expected = BaseFunctionDefinition(
            function_token,
            [Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0))],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("(a,...)end")
        expected = BaseFunctionDefinition(
            function_token,
            [
                self.parse_name("a"),
                Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0)),
            ],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected)
        self.assertEqual(len(parser.context_hints), 0)

    def test_parse_func_expr(self):
        parser = Parser("function()end")
        expected = ExpFunctionDefinition(
            Token(TokenType.FUNCTION, "function", 0, 0),
            [],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        self.assertEqual(parser._parse_exp(), expected)
        self.assertEqual(len(parser.context_hints), 0)

    def test_assign(self):
        parser = Parser('a = "bcd"')
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.NAME, "a", 0, 0),
                [self.parse_name("a")],
                [self.parse_string("bcd")],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser('a,b,c = "bcd"')
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.NAME, "a", 0, 0),
                [
                    self.parse_name("a"),
                    self.parse_name("b"),
                    self.parse_name("c"),
                ],
                [self.parse_string("bcd")],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser('a = "bcd", "def"')
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.NAME, "a", 0, 0),
                [self.parse_name("a")],
                [
                    self.parse_string("bcd"),
                    self.parse_string("def"),
                ],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

    def test_function_stmt(self):
        parser = Parser("a()")
        expected_tree = self.get_chunk(
            FunctionCall(Token(TokenType.NAME, "a", 0, 0), self.parse_name("a"), [])
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        parser = Parser("a[1].b()")
        expected_tree = self.get_chunk(
            FunctionCall(
                Token(TokenType.NAME, "a", 0, 0),
                NamedIndex(
                    Token(TokenType.NAME, "b", 0, 0),
                    Index(
                        Token(TokenType.L_BRACKET, "[", 0, 0),
                        self.parse_name("a"),
                        self.parse_number("1"),
                    ),
                    self.parse_name("b"),
                ),
                [],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)

    def test_method_stmt(self):
        parser = Parser("a:b()")
        expected_tree = self.get_chunk(
            MethodInvocation(
                Token(TokenType.NAME, "a", 0, 0),
                self.parse_name("a"),
                self.parse_name("b"),
                [],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
