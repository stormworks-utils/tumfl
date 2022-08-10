import unittest

from tumfl.AST.String import *


class TestString(unittest.TestCase):
    def test_from_token(self):
        tok = Token(TokenType.STRING, "abc", 1, 1)
        string = String.from_token(tok)
        self.assertEqual(string.value, "abc")
        self.assertIs(string.token, tok)
        self.assertEqual(string.name, "String")
