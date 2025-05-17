import unittest

from tumfl import format, parse
from tumfl.formatter import FormattingStyle
from tumfl.minifier.shorten_names import GetNames
from tumfl.minifier.simplify_expressions import Simplify


class HereComment(FormattingStyle):
    INCLUDE_COMMENTS = False
    KEEP_SEMICOLON = True


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
        test(1,2)
        """
        expected = "; ; ;"
        self.compare_code(code, expected)

    def test_correct_names(self):
        code = """
        function test(a, b)
            foo = a.a + b
            a.a(foo)
            foo = {a = a, b = b, [a] = a, b}
            a:a(foo)
            foo = a:a(foo)
        end
        c, d = 1, 2
        test(c, d)
        """
        expected = """
        ; -- residual function
        c, d = 1, 2
        do
            foo = c.a + d
            c.a(foo)
            foo = {a = c, b = d, [c] = c, d}
            c:a(foo)
            foo = c:a(foo)
        end
        """
        self.compare_code(code, expected)

    def test_not_a_function(self):
        code = """
        a = 2
        a()
        """
        self.compare_code(code, code)


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
        a = - 1
        a = - - - 1
        a = - - .5
        a = - (a - b)
        a = - (a + b)
        """
        expected = """
        a = 1
        a = - 1
        a = - 1
        a = .5
        a = a + b
        a = a - b
        """
        self.compare_code(code, expected)
        code = "a = - (#a)"
        self.compare_code(code, code)
        code = "a = - (a and b)"
        self.compare_code(code, code)

    def compare_not_operators(self, operator_a: str, operator_b: str):
        code = f"a = not (a {operator_a} b)"
        expected = f"a = a {operator_b} b"
        self.compare_code(code, expected)

    def test_not_comparison(self):
        self.compare_not_operators("==", "~=")
        self.compare_not_operators("~=", "==")
        self.compare_not_operators(">", "<=")
        self.compare_not_operators(">=", "<")
        self.compare_not_operators("<", ">=")
        self.compare_not_operators("<=", ">")
        code = "a = not (a and b)"
        self.compare_code(code, code)
        code = "a = not (#a)"
        self.compare_code(code, code)

    def test_else(self):
        code = "a = #foo"
        self.compare_code(code, code)


class TestIf(BaseClass):
    def test_normal(self):
        code = """
        if a then
            b = 1
        else
            b = 2
        end
        """
        self.compare_code(code, code)

    def test_both_full(self):
        code = """
        if true then
            foo = bar
        else
            bar = foo
        end
        """
        expected = """
        do
            foo = bar
        end
        """
        self.compare_code(code, expected)
        code = """
        if false then
            foo = bar
        else
            bar = foo
        end
        """
        expected = """
        do
            bar = foo
        end
        """
        self.compare_code(code, expected)

    def test_half_empty(self):
        code = """
        if true then
            foo = bar
        else
            bar = foo
        end
        """
        expected = """
        do
            foo = bar
        end
        """
        self.compare_code(code, expected)
        code = """
        if false then
            foo = bar
        end
        """
        expected = ";"
        self.compare_code(code, expected)


if __name__ == "__main__":
    unittest.main()
