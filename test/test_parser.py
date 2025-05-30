import unittest

from tumfl.AST import *
from tumfl.AST.base_function_definition import BaseFunctionDefinition
from tumfl.lexer import Lexer, LexerError
from tumfl.parser import Hint, Parser, ParserError
from tumfl.Token import Token, TokenType

EOF_TOKEN: Token = Token(TokenType.EOF, "eof", 0, 0)


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
        return Chunk(statements[0].token, list(statements), None)

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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("-nil")
        expected_tree_u = UnOp.from_token(
            Token(TokenType.MINUS, "-", 0, 0),
            Nil.from_token(Token(TokenType.NIL, "nil", 0, 0)),
        )
        repr_test = repr(expected_tree_u)
        self.assertEqual(parser._parse_exp(), expected_tree_u)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("\n#'a'")
        expected_tree_u = UnOp.from_token(
            Token(TokenType.HASH, "#", 0, 0),
            self.parse_string("a"),
        )
        repr_test = repr(expected_tree_u)
        self.assertEqual(parser._parse_exp(), expected_tree_u)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("1+2+3")
        expected_tree = BinOp.from_token(
            Token(TokenType.PLUS, "+", 0, 0),
            BinOp.from_token(
                Token(TokenType.PLUS, "+", 0, 0),
                self.parse_number("1"),
                self.parse_number("2"),
            ),
            self.parse_number("3"),
        )
        self.assertEqual(parser._parse_exp(), expected_tree)

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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("foo..bar..baz")
        expected_tree = BinOp.from_token(
            Token(TokenType.CONCAT, "..", 0, 0),
            self.parse_name("foo"),
            BinOp.from_token(
                Token(TokenType.CONCAT, "..", 0, 0),
                self.parse_name("bar"),
                self.parse_name("baz"),
            ),
        )
        self.assertEqual(parser._parse_exp(), expected_tree)

    def test_error(self):
        parser = Parser("1+")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected expression")

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
        self.assertEqual(parser.current_token, EOF_TOKEN)

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
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_wrong_token(self):
        parser = Parser("a,b+")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("a=1\nb,c+")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")

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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(2)[1]")
        expected_tree_i = Index(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            self.parse_number("1"),
        )
        repr_test = repr(expected_tree_i)
        self.assertEqual(parser._parse_var(), expected_tree_i)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(2)(1)")
        expected_tree_f = ExpFunctionCall(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_number("2"),
            [self.parse_number("1")],
        )
        repr_test = repr(expected_tree_f)
        self.assertEqual(parser._parse_var(), expected_tree_f)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a:b()")
        expected_tree_m = ExpMethodInvocation(
            Token(TokenType.COLON, "[", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
            [],
        )
        repr_test = repr(expected_tree_m)
        self.assertEqual(parser._parse_var(), expected_tree_m)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_table_constructor(self):
        lbracket_token = Token(TokenType.L_BRACKET, "[", 0, 0)
        lcurl_token = Token(TokenType.L_CURL, "{", 0, 0)
        parser = Parser("{}")
        expected_tree = Table(lcurl_token, [])
        self.assertEqual(parser._parse_table_constructor(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("{a}")
        expected_tree = Table(
            lcurl_token,
            [
                NumberedTableField(
                    Token(TokenType.NAME, "a", 0, 0), self.parse_name("a")
                )
            ],
        )
        repr_test = repr(expected_tree)
        result = parser._parse_table_constructor()
        self.assertEqual(result, expected_tree)
        self.assertEqual(result.token, expected_tree.token)
        self.assertEqual(result.fields[0].token, expected_tree.fields[0].token)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser('{["b"]=c}')
        expected_tree = Table(
            lcurl_token,
            [
                ExplicitTableField(
                    lbracket_token,
                    self.parse_string("b"),
                    self.parse_name("c"),
                )
            ],
        )
        repr_test = repr(expected_tree)
        result = parser._parse_table_constructor()
        self.assertEqual(result, expected_tree)
        self.assertEqual(result.fields[0].token, expected_tree.fields[0].token)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("{a=b}")
        expected_tree = Table(
            lcurl_token,
            [
                NamedTableField(
                    Token(TokenType.NAME, "a", 0, 0),
                    self.parse_name("a"),
                    self.parse_name("b"),
                )
            ],
        )
        repr_test = repr(expected_tree)
        result = parser._parse_table_constructor()
        self.assertEqual(result, expected_tree)
        self.assertEqual(result.fields[0].token, expected_tree.fields[0].token)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("{a, b,}")
        expected_tree = Table(
            lcurl_token,
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("{f'alo'..'xixi'}")
        expected_tree = Table(
            lcurl_token,
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("if }")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.IF, "if", 0, 0), "table constructor", "fields")],
        )
        parser = Parser("{")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected token")
        table_fields_hint = Hint(lcurl_token, "table constructor", "fields")
        self.assertEqual(pe.exception.hints, [table_fields_hint])
        parser = Parser("{[if]=1}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(lbracket_token, "explicit table field", "key expression"),
            ],
        )
        parser = Parser("{[a if=1}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(lbracket_token, "explicit table field", "key expression"),
            ],
        )
        parser = Parser("{[a]if 1}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(lbracket_token, "explicit table field", "value expression"),
            ],
        )
        parser = Parser("{[a]=if}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(lbracket_token, "explicit table field", "value expression"),
            ],
        )
        parser = Parser("{a=if}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(
                    Token(TokenType.NAME, "a", 0, 0),
                    "named table field",
                    "value expression",
                ),
            ],
        )
        parser = Parser("{if}")
        with self.assertRaises(ParserError) as pe:
            parser._parse_table_constructor()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [
                table_fields_hint,
                Hint(
                    Token(TokenType.IF, "if", 0, 0),
                    "numbered table field",
                    "expression",
                ),
            ],
        )

    def test_parse_args(self):
        parser = Parser("()")
        self.assertEqual(parser._parse_args(), [])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser('(a, b, "d", 1)')
        expected_args = [
            self.parse_name("a"),
            self.parse_name("b"),
            self.parse_string("d"),
            self.parse_number("1"),
        ]
        self.assertEqual(parser._parse_args(), expected_args)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(a,b")
        with self.assertRaises(ParserError) as pe:
            parser._parse_args()
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("(a,b,)")
        with self.assertRaises(ParserError) as pe:
            parser._parse_args()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        parser = Parser('"abc"')
        self.assertEqual(parser._parse_args(), [self.parse_string("abc")])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser('{a,"b"}')
        table_result = parser._parse_table_constructor()
        parser = Parser('{a,"b"}')
        self.assertEqual(parser._parse_args(), [table_result])
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(1")
        with self.assertRaises(ParserError) as pe:
            parser._parse_args()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.L_PAREN, "(", 0, 0), "function call", "arguments")],
        )

    def test_parse_names(self):
        parser = Parser("a")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a, b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("b")
        expected_names = [self.parse_name("a")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, Token(TokenType.NAME, "b", 0, 0))
        parser = Parser(",b")
        expected_names = [self.parse_name("a"), self.parse_name("b")]
        self.assertEqual(parser._parse_name_list(self.parse_name("a")), expected_names)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a,")
        with self.assertRaises(ParserError) as pe:
            parser._parse_name_list()
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("a, 1")
        with self.assertRaises(ParserError) as pe:
            parser._parse_name_list()
        self.assertEqual(str(pe.exception), "Unexpected token")

    def test_parse_vararg(self):
        parser = Parser("...")
        expected_tree = Vararg(Token(TokenType.ELLIPSIS, "...", 0, 0))
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_parse_table_expr(self):
        parser = Parser("{a}")
        expected_tree = Parser("{a}")._parse_table_constructor()
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_parse_funcbody(self):
        function_token = Token(TokenType.FUNCTION, "function", 0, 0)
        parser = Parser("()end")
        expected_tree = BaseFunctionDefinition(
            function_token, [], Block(Token(TokenType.END, "end", 0, 0), [], None)
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(a,b)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [self.parse_name("a"), self.parse_name("b")],
            Block(Token(TokenType.END, "end", 0, 0), [], None),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(...)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0))],
            Block(Token(TokenType.END, "end", 0, 0), [], None),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("(a,...)end")
        expected_tree = BaseFunctionDefinition(
            function_token,
            [
                self.parse_name("a"),
                Vararg.from_token(Token(TokenType.ELLIPSIS, "...", 0, 0)),
            ],
            Block(Token(TokenType.END, "end", 0, 0), [], None),
        )
        repr_test = repr(expected_tree)
        parser._add_hint("function", "function")
        self.assertEqual(parser._parse_funcbody(function_token), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("function a if )end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(function_token, "function", "parameters")]
        )
        parser = Parser("function a(if end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(function_token, "function", "body")])

    def test_parse_func_expr(self):
        function_token = Token(TokenType.FUNCTION, "function", 0, 0)
        parser = Parser("function()end")
        expected_tree = ExpFunctionDefinition(
            function_token,
            [],
            Block(Token(TokenType.END, "end", 0, 0), [], None),
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("function(if)end")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(function_token, "function expression", "body")]
        )

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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a, if = b")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected variable")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.COMMA, ",", 0, 0), "assignment", "variables")],
        )
        parser = Parser("(if) = 1")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.L_PAREN, "(", 0, 0), "expression var", "expression")],
        )
        parser = Parser("(foo if = 1")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.L_PAREN, "(", 0, 0), "expression var", "expression")],
        )

    def test_function_stmt(self):
        parser = Parser("a()")
        expected_tree = self.get_chunk(
            FunctionCall(Token(TokenType.NAME, "a", 0, 0), self.parse_name("a"), [])
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)

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
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_method_expr(self):
        parser = Parser("a:b(1,2)")
        expected_tree = ExpMethodInvocation(
            Token(TokenType.NAME, "a", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
            [self.parse_number("1"), self.parse_number("2")],
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser._parse_exp(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a:if()")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.COLON, ":", 0, 0), "invocation", "name")],
        )

    def test_index_expr(self):
        parser = Parser("a[1]")
        expected_tree = Index(
            Token(TokenType.L_BRACKET, "[", 0, 0),
            self.parse_name("a"),
            self.parse_number("1"),
        )
        repr_test = repr(expected_tree)
        result = parser._parse_exp()
        self.assertEqual(result, expected_tree)
        self.assertEqual(result.token, expected_tree.token)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a[if]")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.L_BRACKET, "[", 0, 0), "index", "expression")],
        )
        parser = Parser("a[1 if")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.L_BRACKET, "[", 0, 0), "index", "expression")],
        )

    def test_named_index_expr(self):
        parser = Parser("a.b")
        expected_tree = NamedIndex(
            Token(TokenType.DOT, ".", 0, 0),
            self.parse_name("a"),
            self.parse_name("b"),
        )
        repr_test = repr(expected_tree)
        result = parser._parse_exp()
        self.assertEqual(result, expected_tree)
        self.assertEqual(result.token, expected_tree.token)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("a.if")
        with self.assertRaises(ParserError) as pe:
            parser._parse_exp()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(Token(TokenType.DOT, ".", 0, 0), "index", "name")]
        )

    def test_semicolon(self):
        parser = Parser(";")
        expected_tree = self.get_chunk(Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0)))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("foo")
        with self.assertRaises(ParserError) as pe:
            parser._parse_semi()
        self.assertEqual(str(pe.exception), "Unexpected token")

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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("if a = 2")
        with self.assertRaises(ParserError) as pe:
            parser._parse_local()
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("if = 1")
        with self.assertRaises(ParserError) as pe:
            parser._parse_local_assignment(Token(TokenType.LOCAL, "local", 0, 0))
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.IF, "if", 0, 0), "local assign", "names")],
        )
        parser = Parser("local a, if = 1")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.NAME, "a", 0, 0), "local assign", "name")],
        )
        parser = Parser("local a <if> = 1")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.NAME, "a", 0, 0), "local assign", "name attribute")],
        )
        parser = Parser("local a <a< = 1")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.NAME, "a", 0, 0), "local assign", "name attribute")],
        )
        parser = Parser("local a = if")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.NAME, "a", 0, 0), "local assign", "expressions")],
        )

    def test_parse_local_function(self):
        parser = Parser("local function a ()end")
        expected_tree = self.get_chunk(
            LocalFunctionDefinition(
                Token(TokenType.LOCAL, "local", 0, 0),
                self.parse_name("a"),
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("if a()end")
        with self.assertRaises(ParserError) as pe:
            parser._parse_local_function(Token(TokenType.LOCAL, "local", 0, 0))
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.IF, "if", 0, 0), "local function", "name")],
        )

    def test_parse_unknown_local(self):
        parser = Parser("local and")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected symbol after local")

    def test_parse_function(self):
        function_token = Token(TokenType.FUNCTION, "function", 0, 0)
        parser = Parser("function a ()end")
        expected_tree = self.get_chunk(
            FunctionDefinition(
                function_token,
                [self.parse_name("a")],
                None,
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("function a.b:c ()end")
        expected_tree = self.get_chunk(
            FunctionDefinition(
                function_token,
                [self.parse_name("a"), self.parse_name("b")],
                self.parse_name("c"),
                [],
                Block(Token(TokenType.END, "end", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("foo a()end")
        with self.assertRaises(ParserError) as pe:
            parser._parse_function()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.NAME, "foo", 0, 0), "function", "name")],
        )
        parser = Parser("function a:if()end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(function_token, "function", "method name")]
        )

    def test_parse_iterative_for(self):
        for_token = Token(TokenType.FOR, "for", 0, 0)
        parser = Parser("for a in 2 do end")
        expected_tree = self.get_chunk(
            IterativeFor(
                for_token,
                [self.parse_name("a")],
                [self.parse_number("2")],
                Block(Token(TokenType.DO, "do", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("for a, b in 1, 2 do end")
        expected_tree = self.get_chunk(
            IterativeFor(
                for_token,
                [self.parse_name("a"), self.parse_name("b")],
                [self.parse_number("1"), self.parse_number("2")],
                Block(Token(TokenType.DO, "do", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("foo")
        with self.assertRaises(ParserError) as pe:
            parser._parse_for()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(parser.current_token, "for", "name")]
        )
        in_token = Token(TokenType.IN, "in", 0, 0)
        comma_token = Token(TokenType.COMMA, ",", 0, 0)
        parser = Parser("for a, if in a do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(comma_token, "iterative for", "name list")]
        )
        parser = Parser("for a in if do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints, [Hint(in_token, "iterative for", "expression list")]
        )
        parser = Parser("if 1 if do end")
        with self.assertRaises(ParserError) as pe:
            parser._parse_iterative_for(for_token, self.parse_name("a"))
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.IF, "if", 0, 0), "iterative for", "expression list")],
        )
        parser = Parser("for a in 1 if end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(in_token, "iterative for", "block")])
        parser = Parser("for a,... in 1 do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints,
            [Hint(Token(TokenType.COMMA, ",", 0, 0), "iterative for", "name list")],
        )

    def test_parse_numeric_for(self):
        parser = Parser("for a=1,b do end")
        for_token = Token(TokenType.FOR, "for", 0, 0)
        expected_tree = self.get_chunk(
            NumericFor(
                for_token,
                self.parse_name("a"),
                self.parse_number("1"),
                self.parse_name("b"),
                None,
                Block(Token(TokenType.DO, "do", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("for a=1,b,3 do end")
        expected_tree = self.get_chunk(
            NumericFor(
                for_token,
                self.parse_name("a"),
                self.parse_number("1"),
                self.parse_name("b"),
                self.parse_number("3"),
                Block(Token(TokenType.DO, "do", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("for foo = end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        assign_token = Token(TokenType.ASSIGN, "=", 0, 0)
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints, [Hint(assign_token, "numeric for", "start expression")]
        )
        parser = Parser("for 1,1 do end")
        with self.assertRaises(ParserError) as pe:
            parser._parse_numeric_for(for_token, self.parse_name("a"))
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("for a = 1,end do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(
            pe.exception.hints, [Hint(assign_token, "numeric for", "stop expression")]
        )
        self.assertEqual(str(pe.exception), "Unexpected expression")
        parser = Parser("for a = 1 if 2 do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(
            pe.exception.hints, [Hint(assign_token, "numeric for", "stop expression")]
        )
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("for a = 1,2,end do end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(
            pe.exception.hints, [Hint(assign_token, "numeric for", "step expression")]
        )
        self.assertEqual(str(pe.exception), "Unexpected expression")
        parser = Parser("for a = 1,2 if end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(
            pe.exception.hints, [Hint(assign_token, "numeric for", "block")]
        )
        self.assertEqual(str(pe.exception), "Unexpected token")

    def test_parse_unknown_for(self):
        parser = Parser("for name and")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected for condition")

    def test_parse_if(self):
        parser = Parser("if 1 then end")
        if_token = Token(TokenType.IF, "if", 0, 0)
        then_token = Token(TokenType.THEN, "then", 0, 0)
        else_token = Token(TokenType.ELSE, "else", 0, 0)
        eof_token = EOF_TOKEN
        expected_tree = self.get_chunk(
            If(
                if_token,
                self.parse_number("1"),
                Block(then_token, [], None),
                None,
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, eof_token)
        parser = Parser("if 1 then else end")
        expected_tree = self.get_chunk(
            If(
                if_token,
                self.parse_number("1"),
                Block(then_token, [], None),
                Block(else_token, [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, eof_token)
        parser = Parser("if 1 then elseif 2 then elseif 3 then else end")
        expected_tree = self.get_chunk(
            If(
                if_token,
                self.parse_number("1"),
                Block(then_token, [], None),
                If(
                    Token(TokenType.ELSEIF, "elseif", 0, 0),
                    self.parse_number("2"),
                    Block(Token(TokenType.ELSEIF, "elseif", 0, 0), [], None),
                    If(
                        Token(TokenType.ELSEIF, "elseif", 0, 0),
                        self.parse_number("3"),
                        Block(Token(TokenType.ELSEIF, "elseif", 0, 0), [], None),
                        Block(else_token, [], None),
                    ),
                ),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, eof_token)
        parser = Parser("if then")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(pe.exception.hints, [Hint(if_token, "if", "if condition")])
        parser = Parser("if 1 foo end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(if_token, "if", "if block")])
        parser = Parser("if 1 then elseif end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(pe.exception.hints, [Hint(if_token, "if", "elseif condition")])
        parser = Parser("if 1 then elseif 2 foo end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(if_token, "if", "elseif block")])
        parser = Parser("if 1 then elseif 2 then else until")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(if_token, "if", "else block")])
        parser = Parser("foo 1 then end")
        with self.assertRaises(ParserError):
            parser._parse_if()

    def test_parse_repeat(self):
        parser = Parser("repeat until 1")
        repeat_token = Token(TokenType.REPEAT, "repeat", 0, 0)
        expected_tree = self.get_chunk(
            Repeat(
                repeat_token,
                self.parse_number("1"),
                Block(repeat_token, [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("repeat foo")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected lonely name")
        self.assertEqual(pe.exception.hints, [Hint(repeat_token, "repeat", "block")])
        parser = Parser("repeat end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(
            pe.exception.hints, [Hint(repeat_token, "repeat", "condition")]
        )
        parser = Parser("repeat until")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(
            pe.exception.hints, [Hint(repeat_token, "repeat", "condition")]
        )
        parser = Parser("foo until 1 end")
        with self.assertRaises(ParserError):
            parser._parse_repeat()

    def test_parse_while(self):
        parser = Parser("while 1 do end")
        while_token = Token(TokenType.WHILE, "while", 0, 0)
        expected_tree = self.get_chunk(
            While(
                while_token,
                self.parse_number("1"),
                Block(Token(TokenType.DO, "do", 0, 0), [], None),
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("while")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected expression")
        self.assertEqual(pe.exception.hints, [Hint(while_token, "while", "condition")])
        parser = Parser("while 1 foo end")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        parser = Parser("while 1 do foo")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected lonely name")
        self.assertEqual(pe.exception.hints, [Hint(while_token, "while", "block")])
        parser = Parser("foo 1 do end")
        with self.assertRaises(ParserError):
            parser._parse_while()

    def test_parse_label(self):
        parser = Parser("::label::")
        label_token = Token(TokenType.LABEL_BORDER, "::", 0, 0)
        expected_tree = self.get_chunk(Label(label_token, self.parse_name("label")))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("::")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(label_token, "label", "name")])
        parser = Parser("::label")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(label_token, "label", "end")])
        parser = Parser("foo name::")
        with self.assertRaises(ParserError):
            parser._parse_label()

    def test_parse_goto(self):
        parser = Parser("goto label")
        goto_token = Token(TokenType.GOTO, "goto", 0, 0)
        expected_tree = self.get_chunk(Goto(goto_token, self.parse_name("label")))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("goto")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")
        self.assertEqual(pe.exception.hints, [Hint(goto_token, "goto", "name")])
        parser = Parser("foo label")
        with self.assertRaises(ParserError):
            parser._parse_goto()

    def test_parse_break(self):
        parser = Parser("break")
        expected_tree = self.get_chunk(Break(Token(TokenType.BREAK, "break", 0, 0)))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("foo")
        with self.assertRaises(ParserError):
            parser._parse_break()

    def test_parse_block(self):
        parser = Parser("do end")
        expected_tree = self.get_chunk(Block(Token(TokenType.DO, "do", 0, 0), [], None))
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("do ; end")
        expected_tree = self.get_chunk(
            Block(
                Token(TokenType.DO, "do", 0, 0),
                [Semicolon(Token(TokenType.SEMICOLON, ";", 0, 0))],
                None,
            )
        )
        repr_test = repr(expected_tree)
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("do ;return a end")
        self.assertEqual(parser.parse_chunk(), expected_tree)
        self.assertEqual(len(parser.context_hints), 0)
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
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
        self.assertEqual(parser.current_token, EOF_TOKEN)
        parser = Parser("do")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected token")

    def test_unexpected_statement(self):
        parser = Parser("+")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected statement")

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
        self.assertEqual(parser.current_token, EOF_TOKEN)

    def test_lonely_var(self):
        parser = Parser("a")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        self.assertEqual(str(pe.exception), "Unexpected lonely name")

    def test_lonely_return(self):
        parser = Parser("do return end")
        expected_tree = self.get_chunk(Block(Token(TokenType.DO, "do", 0, 0), [], []))
        self.assertEqual(parser.parse_chunk(), expected_tree)
        parser = Parser("do end")
        expected_tree = self.get_chunk(Block(Token(TokenType.DO, "do", 0, 0), [], None))
        self.assertEqual(parser.parse_chunk(), expected_tree)

    def test_accepts_as(self):
        parser = Parser("as = 'foo'")
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.ASSIGN, "=", 0, 0),
                [self.parse_name("as")],
                [self.parse_string("foo")],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)
        parser = Parser("as = 'foo'", typed=True)
        with self.assertRaises(ParserError):
            parser.parse_chunk()

    def test_unicode_errors(self):
        parser = Parser("a = '\\xff'")
        with self.assertRaises(LexerError):
            parser.parse_chunk()
        parser = Parser("a = '\\xff'", ignore_unicode_errors=True)
        expected_tree = self.get_chunk(
            Assign(
                Token(TokenType.ASSIGN, "=", 0, 0),
                [self.parse_name("a")],
                [self.parse_string("")],
            )
        )
        self.assertEqual(parser.parse_chunk(), expected_tree)

    def test_error_message(self):
        parser = Parser("foo()\nbar()\na = ()\nbaz()\n")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        e = pe.exception
        self.assertMultiLineEqual(
            e.full_error,
            "Error on line 3:\nbar()\na = ()\n     ^\nUnexpected expression\nhints: <assignment> expressions (3:3) -> <expression var> expression (3:5)\n",
        )
        self.assertEqual(str(e), "Unexpected expression")
        self.assertEqual(len(e.hints), 2)
        self.assertEqual(e.token, Token(TokenType.R_PAREN, ")", 0, 0))
        parser = Parser("a = ()\nbaz()\n")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        e = pe.exception
        self.assertMultiLineEqual(
            e.full_error,
            "Error on line 1:\na = ()\n     ^\nUnexpected expression\nhints: <assignment> expressions (1:3) -> <expression var> expression (1:5)\n",
        )
        parser = Parser("bar()\na = ()\n")
        with self.assertRaises(ParserError) as pe:
            parser.parse_chunk()
        e = pe.exception
        self.assertMultiLineEqual(
            e.full_error,
            "Error on line 2:\nbar()\na = ()\n     ^\nUnexpected expression\nhints: <assignment> expressions (2:3) -> <expression var> expression (2:5)\n",
        )

    def test_hint(self):
        hint_a = Hint(
            Token(TokenType.NAME, "a", 0, 0), "test hint", "test hint description"
        )
        hint_b = Hint(
            Token(TokenType.NAME, "b", 0, 0), "test hint b", "test hint description b"
        )
        self.assertNotEqual(hint_a, hint_b)
        self.assertNotEqual(hint_a, True)
        self.assertEqual(
            hint_a,
            Hint(
                Token(TokenType.NAME, "a", 0, 0), "test hint", "test hint description"
            ),
        )
        self.assertNotEqual(
            hint_a,
            Hint(
                Token(TokenType.NAME, "a", 0, 0), "test hint", "different description"
            ),
        )
        self.assertNotEqual(
            hint_a,
            Hint(
                Token(TokenType.NAME, "b", 0, 0), "test hint", "test hint description"
            ),
        )
        self.assertNotEqual(
            hint_a,
            Hint(
                Token(TokenType.NAME, "a", 0, 0), "test hint b", "test hint description"
            ),
        )
        self.assertEqual(repr(hint_a), "<test hint> test hint description (0:0)")


class EmptyTest(unittest.TestCase):
    def test_empty(self):
        parser = Parser("")
        parser.parse_chunk()
