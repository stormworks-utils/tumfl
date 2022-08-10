import unittest

from tumfl.AST.Number import *


class TestNumber(unittest.TestCase):
    def test_from_token(self):
        tok = Token(TokenType.NUMBER, (False, "2", "1", "+10", None), 1, 1)
        nmb = Number.from_token(tok)
        self.assertFalse(nmb.is_hex)
        self.assertEqual(nmb.integer_part, "2")
        self.assertEqual(nmb.fractional_part, "1")
        self.assertEqual(nmb.exponent, "+10")
        self.assertIs(nmb.float_offset, None)
        self.assertEqual(nmb.name, "Number")
        self.assertIs(nmb.token, tok)
