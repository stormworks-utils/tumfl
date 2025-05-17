import unittest

from tumfl import format, parse
from tumfl.formatter import FormattingStyle
from tumfl.minifier.shorten_names import GetNames
from tumfl.minifier.simplify_expressions import Simplify


class HereComment(FormattingStyle):
    INCLUDE_COMMENTS = False


class BaseClass(unittest.TestCase):
    def compare_code(self, code: str, expected: str):
        ast = parse(code)
        GetNames()(ast)
        Simplify()(ast)
        self.assertMultiLineEqual(
            format(ast, HereComment), format(parse(expected), HereComment)
        )


class TestInlineFunction(BaseClass):

    def test_2_reads(self):
        code = """
        function test(a, b)
            foo = a + b
        end
        a, b = 1, 2
        test(a, b)
        test(a, b)
        """
        self.compare_code(code, code)

    def test_2_writes(self):
        code = """
        function test(a, b)
            foo = a + b
        end
        function test(a, b)
            bar = a + b
        end
        a, b = 1, 2
        test(a, b)
        """
        self.compare_code(code, code)

    def test_non_name(self):
        code = """
        function test(a, b)
            foo = a + b
        end
        a = 1
        test(a, 2)
        """
        self.compare_code(code, code)

    def test_has_return(self):
        code = """
        function test(a, b)
            return a + b
        end
        a, b = 1, 2
        test(a, b)
        """
        self.compare_code(code, code)

    def test_allowed(self):
        code = """
        function test(a, b)
            foo = a + b
        end
        c, d = 1, 2
        test(c, d)
        """
        expected = """
        ; -- residual function
        c, d = 1, 2
        do -- block is preserved
            foo = c + d
        end
        """
        self.compare_code(code, expected)

    def test_empty_function(self):
        code = """
        function test(a,b)
        end
        test(1,2)
        """
        expected = """
        ;
        ;
        """
        self.compare_code(code, expected)


class TestUnOp(BaseClass):
    def test_not(self):
        code = """
        a = not not 1
        """
        expected = """
        a = 1
        """
        self.compare_code(code, expected)

    def test_negative(self):
        code = """
        a = - - 1
        """
        expected = """
        a = 1
        """
        self.compare_code(code, expected)

    def compare_not_operators(self, operator_a: str, operator_b: str):
        code = f"""
        a = not (a {operator_a} b)
        """
        expected = f"""
        a = a {operator_b} b
        """
        self.compare_code(code, expected)

    def test_not_comparison(self):
        self.compare_not_operators("==", "~=")
        self.compare_not_operators("~=", "==")
        self.compare_not_operators(">", "<=")
        self.compare_not_operators(">=", "<")
        self.compare_not_operators("<", ">=")
        self.compare_not_operators("<=", ">")


if __name__ == "__main__":
    unittest.main()
