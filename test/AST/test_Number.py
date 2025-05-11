import unittest

from tumfl.AST.expression.number import *


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
        self.assertEqual(nmb.to_int(), None)
        self.assertEqual(nmb.to_float(), 2.1e10)
        nmb = Number(tok, False, None, "2", "-5", None)
        self.assertEqual(nmb.to_int(), None)
        self.assertEqual(nmb.to_float(), 0.2e-5)
        nmb = Number(tok, True, None, "2", None, "-5")
        self.assertEqual(nmb.to_float(), float.fromhex("0x1.2p-5"))
        nmb = Number(tok, True, "5", "1231f", None, "5")
        self.assertEqual(nmb.to_float(), float.fromhex("5.1231fp5"))
        nmb = Number(tok, False, "43534", None, None, None)
        self.assertEqual(nmb.to_float(), 43534.0)
        self.assertEqual(nmb.to_int(), 43534)
        nmb = Number(tok, True, "43534f", None, None, None)
        self.assertEqual(nmb.to_float(), 0x43534F)
        self.assertEqual(nmb.to_int(), 0x43534F)
