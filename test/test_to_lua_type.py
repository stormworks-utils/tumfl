import unittest

from tumfl import parse
from tumfl.AST import Assign, Chunk
from tumfl.to_lua_type import Retype, to_lua_type
from tumfl.to_python_type import NilVal


class TestToLuaType(unittest.TestCase):
    def run_test(self, python_type: Retype, expected: str):
        expected_ast = parse(f"a = {expected}")
        assert isinstance(expected_ast, Chunk)
        first_statement = expected_ast.statements[0]
        assert isinstance(first_statement, Assign)
        expected_value = first_statement.expressions[0]
        result = to_lua_type(python_type)
        self.assertEqual(result, expected_value)

    def test_string(self):
        self.run_test("hello", '"hello"')

    def test_integer(self):
        self.run_test(1, "1")
        self.run_test(-50, "-50")

    def test_float(self):
        self.run_test(1.0, "1.0")
        self.run_test(-50.5, "-50.5")
        self.run_test(1.23, "1.23")
        self.run_test(-50.5, "-50.5")

    def test_nil(self):
        self.run_test(NilVal(), "nil")

    def test_boolean(self):
        self.run_test(True, "true")
        self.run_test(False, "false")

    def test_list(self):
        self.run_test([1, 2, 3], "{1, 2, 3}")
        self.run_test([1, 2, "a"], '{1, 2, "a"}')
        self.run_test([1, 2, NilVal()], "{1, 2, nil}")

    def test_dictionary(self):
        self.run_test({"a": 1, "b": 2}, "{a = 1, b = 2}")
        self.run_test({1: 1, 2: 2}, "{1, 2}")
        self.run_test({0: 1, 1: 2}, "{2, [0] = 1}")
        self.run_test({0: NilVal(), "a": NilVal()}, "{[0] = nil, a = nil}")
        self.run_test({"1foo": 2}, '{["1foo"] = 2}')


if __name__ == "__main__":
    unittest.main()
