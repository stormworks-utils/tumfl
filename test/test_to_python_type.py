import unittest

from tumfl import parse
from tumfl.AST import Assign, Chunk
from tumfl.to_python_type import NilVal, Retype, ToPythonType

# TODO: Do full test by testing against interpreter, which in turn is tested against lua tests


class BaseClass(unittest.TestCase):
    def run_test(self, code: str, expected: Retype):
        ast = parse(f"a={code}")
        assert isinstance(ast, Chunk)
        first_node = ast.statements[0]
        assert isinstance(first_node, Assign)
        result = ToPythonType()(first_node.expressions[0])
        self.assertEqual(result, expected)
        self.assertIsInstance(result, type(expected))


class TestBoolean(BaseClass):
    def test_true(self):
        self.run_test("true", True)

    def test_false(self):
        self.run_test("false", False)


class TestNil(BaseClass):
    def test_nil(self):
        self.run_test("nil", NilVal())


class TestNumber(BaseClass):
    def test_integer(self):
        self.run_test("1", 1)

    def test_float(self):
        self.run_test("1.0", 1.0)
        self.run_test("1.23", 1.23)

    def test_hexadecimal(self):
        self.run_test("0x1", 1)
        self.run_test("0x1.23", 1.13671875)
        self.run_test("0x1.23p-4", 0.071044921875)
        self.run_test("0x1.23p4", 18.1875)


class TestString(BaseClass):
    def test_string(self):
        self.run_test('"hello"', "hello")


class TestTable(BaseClass):
    def test_key_table(self):
        self.run_test("{a = 1, b = 2}", {"a": 1, "b": 2})

    def test_not_defined(self):
        self.run_test("{a = 1, b = b}", None)

    def test_list(self):
        self.run_test("{1, 2, 3}", [1, 2, 3])
        self.run_test("{1, 2, a = 3}", {1: 1, 2: 2, "a": 3})
        self.run_test("{1, 2, 3, [4] = 4}", [1, 2, 3, 4])
        self.run_test("{1, 2, [5] = 5}", {1: 1, 2: 2, 5: 5})
        self.run_test("{[0] = 1, 1, 2}", {0: 1, 1: 1, 2: 2})

    def test_explicit_field(self):
        self.run_test('{["foo"] = 1, [2] = 2}', {"foo": 1, 2: 2})
        self.run_test("{[a] = 1}", None)


class TestUnOp(BaseClass):
    def test_not(self):
        self.run_test("not true", False)
        self.run_test("not false", True)
        self.run_test("not nil", True)
        self.run_test("not 1", False)
        self.run_test("not 0", False)
        self.run_test('not ""', False)
        self.run_test('not "hello"', False)

    def test_minus(self):
        self.run_test("-1", -1)
        self.run_test("-1.0", -1.0)
        self.run_test("-0x1", -1)
        self.run_test("-{1}", None)

    def test_bit_not(self):
        self.run_test("~1", -2)
        self.run_test("~0x1", -2)
        self.run_test("~0x1.23", -2)
        self.run_test("~{1}", None)

    def test_hash(self):
        self.run_test("#1", None)
        self.run_test('#"hello"', 5)
        self.run_test("#{1, 2, 3}", 3)
        self.run_test("#{a = 1, b = 2}", 2)
        self.run_test("#{[a] = 1}", None)


class TestBinOp(BaseClass):
    def test_invalid(self):
        self.run_test("a + b", None)

    def test_plus(self):
        self.run_test("1 + 2", 3)
        self.run_test("1.0 + 2.0", 3.0)
        self.run_test('"hello" + " world"', None)
        self.run_test("{1} + {2}", None)

    def test_minus(self):
        self.run_test("1 - 2", -1)
        self.run_test("1.0 - 2.0", -1.0)
        self.run_test('"hello" - " world"', None)
        self.run_test("{1} - {2}", None)

    def test_mult(self):
        self.run_test("1 * 2", 2)
        self.run_test("1.0 * 2.0", 2.0)
        self.run_test('"hello" * " world"', None)

    def test_div(self):
        self.run_test("1 / 2", 0.5)
        self.run_test("1.0 / 2.0", 0.5)
        self.run_test("1 / 1", 1.0)
        self.run_test('"hello" / " world"', None)

    def test_mod(self):
        self.run_test("1 % 2", 1)
        self.run_test("1.0 % 2.0", 1.0)
        self.run_test('"hello" % " world"', None)

    def test_integer_div(self):
        self.run_test("1 // 2", 0)
        self.run_test("2 // 2.0", 1)
        self.run_test('"hello" // " world"', None)

    def test_power(self):
        self.run_test("2 ^ 3", 8.0)
        self.run_test("2.0 ^ 3.0", 8.0)
        self.run_test("2 ^ 3.0", 8.0)
        self.run_test('"hello" ^ " world"', None)

    def test_concat(self):
        self.run_test('"hello" .. " world"', "hello world")
        self.run_test("{1} .. {2}", None)
        self.run_test("1 .. 2", "12")
        self.run_test('1 .. " hello"', "1 hello")

    def test_bit_and(self):
        self.run_test("1 & 2", 0)
        self.run_test("1.0 & 2.0", 0)
        self.run_test("1.5 & 2.0", None)
        self.run_test("1 & 3", 1)
        self.run_test('"hello" & " world"', None)

    def test_bit_or(self):
        self.run_test("1 | 2", 3)
        self.run_test("1.0 | 2.0", 3)
        self.run_test("1.5 | 2.0", None)
        self.run_test("1 | 3", 3)
        self.run_test('"hello" | " world"', None)

    def test_bit_xor(self):
        self.run_test("1 ~ 2", 3)
        self.run_test("1.0 ~ 2.0", 3)
        self.run_test("1.0 ~ 2.5", None)
        self.run_test("1 ~ 3", 2)
        self.run_test('"hello" ~ " world"', None)

    def test_shift_left(self):
        self.run_test("1 << 2", 4)
        self.run_test("1.0 << 2.0", 4)
        self.run_test("1.5 << 2.0", None)
        self.run_test('"hello" << " world"', None)

    def test_shift_right(self):
        self.run_test("1 >> 2", 0)
        self.run_test("4 >> 2", 1)
        self.run_test("1.0 >> 2.0", 0)
        self.run_test("1.5 >> 2.0", None)
        self.run_test('"hello" >> " world"', None)

    def test_equals(self):
        self.run_test("1 == 2", False)
        self.run_test("1.0 == 2.0", False)
        self.run_test('"hello" == " world"', False)
        # objects are compared by id by default
        self.run_test("{1} == {2}", None)
        self.run_test("1 == 1", True)
        self.run_test('"hello" == "hello"', True)

    def test_not_equals(self):
        self.run_test("1 ~= 2", True)
        self.run_test("1.0 ~= 2.0", True)
        self.run_test('"hello" ~= " world"', True)
        # objects are compared by id by default
        self.run_test("{1} ~= {2}", None)
        self.run_test("1 ~= 1", False)
        self.run_test('"hello" ~= "hello"', False)

    def test_greater_than(self):
        self.run_test("1 > 2", False)
        self.run_test("1.0 > 2.0", False)
        self.run_test('"hello" > "world"', False)
        self.run_test("{1} > {2}", None)
        self.run_test("1 > 1", False)
        self.run_test('"hello" > "hello"', False)
        self.run_test('"hello" > 1', None)

    def test_greater_equals(self):
        self.run_test("1 >= 2", False)
        self.run_test("1.0 >= 2.0", False)
        self.run_test('"hello" >= "world"', False)
        self.run_test("{1} >= {2}", None)
        self.run_test("1 >= 1", True)
        self.run_test('"hello" >= "hello"', True)
        self.run_test('"hello" >= 1', None)

    def test_less_than(self):
        self.run_test("1 < 2", True)
        self.run_test("1.0 < 2.0", True)
        self.run_test('"hello" < "world"', True)
        self.run_test("{1} < {2}", None)
        self.run_test("1 < 1", False)
        self.run_test('"hello" < "hello"', False)
        self.run_test('"hello" < 1', None)

    def test_less_equals(self):
        self.run_test("1 <= 2", True)
        self.run_test("1.0 <= 2.0", True)
        self.run_test('"hello" <= "world"', True)
        self.run_test("{1} <= {2}", None)
        self.run_test("1 <= 1", True)
        self.run_test('"hello" <= "hello"', True)
        self.run_test('"hello" <= 1', None)

    def test_and(self):
        self.run_test("true and true", True)
        self.run_test("true and false", False)
        self.run_test("false and true", False)
        self.run_test("false and false", False)
        self.run_test('"hello" and "world"', "world")
        self.run_test("{1} and {2}", [2])
        self.run_test("0 and {5}", [5])
        self.run_test("nil and {5}", NilVal())

    def test_or(self):
        self.run_test("true or true", True)
        self.run_test("true or false", True)
        self.run_test("false or true", True)
        self.run_test("false or false", False)
        self.run_test('"hello" or "world"', "hello")
        self.run_test("{1} or {2}", [1])
        self.run_test("0 or {5}", 0)
        self.run_test("nil or {5}", [5])


if __name__ == "__main__":
    unittest.main()
