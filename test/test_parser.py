import unittest

from tumfl.AST import *
from tumfl.Token import Token, TokenType
from tumfl.parser import Parser
from tumfl.lexer import Lexer


class TestParser(unittest.TestCase):
    @staticmethod
    def parse_number(to_parse: str) -> Number:
        lex = Lexer(to_parse)
        return Number.from_token(lex.get_next_token())

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
            String.from_token(Token(TokenType.STRING, "a", 0, 0)),
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
        with self.assertRaises(NotImplementedError):
            parser._parse_exp()
