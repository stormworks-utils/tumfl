import unittest

from tumfl import minify, parse, format


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
        a = foo.bar
        local b = a()
        local c = a()
        a(b, c)
        """
        self.assertEqual(formatted_code, format(parse(expected_code)))


if __name__ == '__main__':
    unittest.main()
