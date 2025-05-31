import unittest

from tumfl import format, minify, parse


class TestMinifier(unittest.TestCase):
    def test_use_removed_name(self):
        code = """
        -- will be removed
        local a = foo.bar()
        local b = foo.bar()
        local c = foo.bar()
        foo.bar(b, c)
        """
        ast = parse(code)
        minify(ast)
        formatted_code = format(ast)
        expected_code = """
        local b, c
        a = foo.bar
        b = a()
        c = a()
        a(b, c)
        """
        self.assertMultiLineEqual(formatted_code, format(parse(expected_code)))

    def test_local_assign(self):
        code = """
        b = 2
        local a = 1
        local b = b
        local c = a + b
        foo(c)
        """
        ast = parse(code)
        minify(ast)
        formatted_code = format(ast)
        expected_code = """
        local b, c, d
        a = 2
        b = 1
        c = a
        d = b + c
        foo(d)
        """
        self.assertMultiLineEqual(formatted_code, format(parse(expected_code)))


if __name__ == "__main__":
    unittest.main()
