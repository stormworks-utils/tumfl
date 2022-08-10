import unittest

from tumfl.AST.Variable import *


class TestVariable(unittest.TestCase):
    def test_from_token(self):
        tok = Token(TokenType.NAME, "def", 1, 1)
        variable = Variable.from_token(tok)
        self.assertEqual(variable.id, "def")
        self.assertEqual(variable.name, "Variable")
        self.assertIs(variable.token, tok)
