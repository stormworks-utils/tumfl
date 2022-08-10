import unittest

from tumfl.AST.Boolean import *


class TestBoolean(unittest.TestCase):
    def test_from_token(self):
        tok = Token(TokenType.TRUE, "true", 1, 1)
        boolean = Boolean.from_token(tok)
        self.assertTrue(boolean.value)
        self.assertIs(boolean.token, tok)
        self.assertEqual(boolean.name, "Boolean")
        tok = Token(TokenType.FALSE, "false", 1, 1)
        boolean = Boolean.from_token(tok)
        self.assertFalse(boolean.value)
