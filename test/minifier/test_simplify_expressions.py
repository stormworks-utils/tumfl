import unittest
from tumfl import parse
from tumfl.minifier.simplify_expressions import Simplify
from tumfl.minifier.shorten_names import GetNames


class TestInlineFunction(unittest.TestCase):
    def compare_code(self, code: str, expected: str):
        ast = parse(code)
        GetNames()(ast)
        Simplify()(ast)
        self.assertEqual(ast, parse(expected))

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


if __name__ == '__main__':
    unittest.main()
