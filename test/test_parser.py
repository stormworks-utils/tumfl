import unittest

from tumfl.AST import *
from tumfl.AST.BaseFunctionDefinition import BaseFunctionDefinition
from tumfl.lexer import Lexer
from tumfl.parser import Parser, ParserError
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("-nil")
        expected_tree = UnOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            Nil.from_token(Token(TokenType.NIL, "nil", 0, 0)),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("\n#'a'")
        expected_tree = UnOp.from_token(
            Token(TokenType.HASH, "#", 0, 0),
            self.parse_string("a"),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("2^-2+s")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            BinOp.from_token(
                Token(TokenType.EXPONENT, "#", 0, 0),
                self.parse_number("2"),
                UnOp.from_token(
                    Token(TokenType.MINUS, "-", 0, 0), self.parse_number("2")
                ),
            ),
            self.parse_name("s"),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_error(self):
        parser = Parser("1+")
        with self.assertRaises(ParserError):
            parser._parse_exp()

    def test_unary_expr(self):
        parser = Parser("1- -2")
        expected_tree = BinOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            self.parse_number("1"),
            UnOp.from_token(Token(TokenType.MINUS, "-", 0, 0), self.parse_number("2")),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_len_operator(self):
        parser = Parser("\n#a + 1")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            UnOp.from_token(
                Token(TokenType.HASH, "#", 0, 0),
                self.parse_name("a"),
            ),
            self.parse_number("1"),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_wrong_token(self):
        parser = Parser("a,b+")
        with self.assertRaises(ParserError):
            parser.parse_chunk()
        parser = Parser("a=1\nb,c+")
        with self.assertRaises(ParserError):
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(2)[1]")
        expected_tree = Index(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            self.parse_number("1"),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(2)(1)")
        expected_tree = ExpFunctionCall(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            [self.parse_number("1")],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("a:b()")
        expected_tree = ExpMethodInvocation(
            Token(TokenType.COLON, "[", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
            [],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_var(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_table_constructor(self):
        parser = Parser("{}")
        expected_tree = Table(Token(TokenType.L_CURL, "{", 0, 0), [])
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("{a}")
        expected_tree = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NumberedTableField(
                    Token(TokenType.NAME, "a", 0, 0), self.parse_name("a")
                )
            ],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser('{["b"]=c}')
        expected_tree = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                ExplicitTableField(
                    Token(TokenType.L_BRACKET, "[", 0, 0),
                    self.parse_string("b"),
                    self.parse_name("c"),
                )
            ],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("{a=b}")
        expected_tree = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NamedTableField(
                    Token(TokenType.NAME, "a", 0, 0),
                    self.parse_name("a"),
                    self.parse_name("b"),
                )
            ],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("{a, b,}")
        expected_tree = Table(
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("{f'alo'..'xixi'}")
        expected_tree = Table(
            Token(TokenType.L_CURL, "{", 0, 0),
            [
                NumberedTableField(
                    Token(TokenType.NAME, "f", 0, 0),
                    BinOp.from_token(
                        Token(TokenType.CONCAT, "..", 0, 0),
                        ExpFunctionCall(
                            Token(TokenType.FUNCTION, "function", 0, 0),
                            self.parse_name("f"),
                            [self.parse_string("alo")],
                        ),
                        self.parse_string("xixi"),
                    ),
                )
            ],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_args(self):
        parser = Parser("()")
        self.assertEqual(parser._parse_args(), [])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser('(a, b, "d", 1)')
        expected_args = [
            self.parse_name("a"),
            self.parse_name("b"),
            self.parse_string("d"),
            self.parse_number("1"),
        ]
        self.assertEqual(parser._parse_args(), expected_args)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(a,b")
        with self.assertRaises(ParserError):
            parser._parse_args()
        parser = Parser("(a,b,)")
        with self.assertRaises(ParserError):
            parser._parse_args()
        parser = Parser('"abc"')
        self.assertEqual(parser._parse_args(), [self.parse_string("abc")])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser('{a,"b"}')
        table_result = parser._parse_table_constructor()
        parser = Parser('{a,"b"}')
        self.assertEqual(parser._parse_args(), [table_result])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_names(self):
        parser = Parser("a")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("a, b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.NAME, "b", 0, 0))
        parser = Parser(",b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("a,")
        with self.assertRaises(ParserError):
            parser._parse_name_list()
        parser = Parser("a, 1")
        with self.assertRaises(ParserError):
            parser._parse_name_list()

    def test_parse_vararg(self):
        parser = Parser("...")
        expected_tree = Vararg(Token(TokenType.ELLIPSIS, "...", 0, 0))
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_table_expr(self):
        parser = Parser("{a}")
        expected_tree = Parser("{a}")._parse_table_constructor()
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_funcbody(self):
        function_token = Token(TokenType.FUNCTION, "function", 0, 0)
        parser = Parser("()end")
        expected_tree = BaseFunctionDefinition(
            function_token, [], Block(Token(TokenType.END, "end", 0, 0), [], [])
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(a,b)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [self.parse_name("a"), self.parse_name("b")],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(...)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0))],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("(a,...)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [
                self.parse_name("a"),
                Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0)),
            ],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_func_expr(self):
        parser = Parser("function()end")
        expected_tree = ExpFunctionDefinition(
            Token(TokenType.FUNCTION, "function", 0, 0),
            [],
            Block(Token(TokenType.END, "end", 0, 0), [], []),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_assign(self):
        parser = Parser('a = "bcd"')
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.NAME, "a", 0, 0),
                [self.parse_name("a")],
                [self.parse_string("bcd")],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_function_stmt(self):
        parser = Parser("a()")
        expected_tree = self.get_chunk(
            FunctionCall(Token(TokenType.NAME, "a", 0, 0), self.parse_name("a"), [])
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
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
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

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
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_semicolon(self):
        parser = Parser(";")
        expected_tree = self.get_chunk(Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0)))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_local_assignment(self):
        parser = Parser("local a, b")
        expected_tree = self.get_chunk(
            LocalAssign(
                Token(TokenType.LOCAL, "local", 0, 0),
                [
                    AttributedName(self.parse_name("a")),
                    AttributedName(self.parse_name("b")),
                ],
                None,
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("local a <const>, b <final>")
        expected_tree = self.get_chunk(
            LocalAssign(
                Token(TokenType.LOCAL, "local", 0, 0),
                [
                    AttributedName(self.parse_name("a"), self.parse_name("const")),
                    AttributedName(self.parse_name("b"), self.parse_name("final")),
                ],
                None,
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("local a=d,e")
        expected_tree = self.get_chunk(
            LocalAssign(
                Token(TokenType.LOCAL, "local", 0, 0),
                [AttributedName(self.parse_name("a"))],
                [self.parse_name("d"), self.parse_name("e")],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_local_function(self):
        parser = Parser("local function a ()end")
        expected_tree = self.get_chunk(
            LocalFunctionDefinition(
                Token(TokenType.LOCAL, "local", 0, 0),
                self.parse_name("a"),
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_unknown_local(self):
        parser = Parser("local and")
        with self.assertRaises(ParserError):
            parser.parse_chunk()

    def test_parse_function(self):
        parser = Parser("function a ()end")
        expected_tree = self.get_chunk(
            FunctionDefinition(
                Token(TokenType.FUNCTION, "function", 0, 0),
                [self.parse_name("a")],
                None,
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("function a.b:c ()end")
        expected_tree = self.get_chunk(
            FunctionDefinition(
                Token(TokenType.FUNCTION, "function", 0, 0),
                [self.parse_name("a"), self.parse_name("b")],
                self.parse_name("c"),
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_iterative_for(self):
        parser = Parser("for a in 2 do end")
        expected_tree = self.get_chunk(
            IterativeFor(
                Token(TokenType.FOR, "for", 0, 0),
                [self.parse_name("a")],
                [self.parse_number("2")],
                Block(Token(TokenType.DO, "do", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("for a, b in 1, 2 do end")
        expected_tree = self.get_chunk(
            IterativeFor(
                Token(TokenType.FOR, "for", 0, 0),
                [self.parse_name("a"), self.parse_name("b")],
                [self.parse_number("1"), self.parse_number("2")],
                Block(Token(TokenType.DO, "do", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_numeric_for(self):
        parser = Parser("for a=1,b do end")
        expected_tree = self.get_chunk(
            NumericFor(
                Token(TokenType.FOR, "for", 0, 0),
                self.parse_name("a"),
                self.parse_number("1"),
                self.parse_name("b"),
                None,
                Block(Token(TokenType.DO, "do", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("for a=1,b,3 do end")
        expected_tree = self.get_chunk(
            NumericFor(
                Token(TokenType.FOR, "for", 0, 0),
                self.parse_name("a"),
                self.parse_number("1"),
                self.parse_name("b"),
                self.parse_number("3"),
                Block(Token(TokenType.DO, "do", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_unknown_for(self):
        parser = Parser("for name and")
        with self.assertRaises(ParserError):
            parser.parse_chunk()

    def test_parse_if(self):
        parser = Parser("if 1 then end")
        expected_tree = self.get_chunk(
            If(
                Token(TokenType.IF, "if", 0, 0),
                self.parse_number("1"),
                Block(Token(TokenType.THEN, "then", 0, 0), [], []),
                None,
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("if 1 then else end")
        expected_tree = self.get_chunk(
            If(
                Token(TokenType.IF, "if", 0, 0),
                self.parse_number("1"),
                Block(Token(TokenType.THEN, "then", 0, 0), [], []),
                Block(Token(TokenType.ELSE, "else", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("if 1 then elseif 2 then else end")
        expected_tree = self.get_chunk(
            If(
                Token(TokenType.IF, "if", 0, 0),
                self.parse_number("1"),
                Block(Token(TokenType.THEN, "then", 0, 0), [], []),
                If(
                    Token(TokenType.ELSEIF, "elseif", 0, 0),
                    self.parse_number("2"),
                    Block(Token(TokenType.ELSEIF, "elseif", 0, 0), [], []),
                    Block(Token(TokenType.ELSE, "else", 0, 0), [], []),
                ),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_repeat(self):
        parser = Parser("repeat until 1")
        expected_tree = self.get_chunk(
            Repeat(
                Token(TokenType.REPEAT, "repeat", 0, 0),
                self.parse_number("1"),
                Block(Token(TokenType.REPEAT, "repeat", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_while(self):
        parser = Parser("while 1 do end")
        expected_tree = self.get_chunk(
            While(
                Token(TokenType.WHILE, "while", 0, 0),
                self.parse_number("1"),
                Block(Token(TokenType.DO, "do", 0, 0), [], []),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_label(self):
        parser = Parser("::label::")
        expected_tree = self.get_chunk(
            Label(Token(TokenType.LABEL_BORDER, "::", 0, 0), self.parse_name("label"))
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_goto(self):
        parser = Parser("goto label")
        expected_tree = self.get_chunk(
            Goto(Token(TokenType.GOTO, "goto", 0, 0), self.parse_name("label"))
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_break(self):
        parser = Parser("break")
        expected_tree = self.get_chunk(Break(Token(TokenType.BREAK, "break", 0, 0)))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_parse_block(self):
        parser = Parser("do end")
        expected_tree = self.get_chunk(Block(Token(TokenType.DO, "do", 0, 0), [], []))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("do ; end")
        expected_tree = self.get_chunk(
            Block(
                Token(TokenType.DO, "do", 0, 0),
                [Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0))],
                [],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("do ;return a; end")
        expected_tree = self.get_chunk(
            Block(
                Token(TokenType.DO, "do", 0, 0),
                [Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0))],
                [self.parse_name("a")],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("do ;return a end")
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("do ;return ; end")
        expected_tree = self.get_chunk(
            Block(
                Token(TokenType.DO, "do", 0, 0),
                [Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0))],
                [],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))
        parser = Parser("do return end")
        expected_tree = self.get_chunk(
            Block(
                Token(TokenType.DO, "do", 0, 0),
                [],
                [],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))

    def test_unexpected_statement(self):
        parser = Parser("+")
        with self.assertRaises(ParserError):
            parser.parse_chunk()

    def test_weird_stuff(self):
        parser = Parser("assert()()")
        expected_tree = self.get_chunk(
            FunctionCall(
                Token(TokenType.NAME, "assert", 0, 0),
                ExpFunctionCall(
                    Token(TokenType.NAME, "assert", 0, 0), self.parse_name("assert"), []
                ),
                [],
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.EOF, "eof", 0, 0))


class EmptyTest(unittest.TestCase):
    def test_empty(self):
        parser = Parser("")
        parser.parse_chunk()
