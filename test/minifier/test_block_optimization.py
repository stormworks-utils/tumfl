import unittest

from tumfl import format, parse
from tumfl.minifier.block_optimization import Optimize


class TestBlockOptimization(unittest.TestCase):
    def run_test(self, code: str, expected: str):
        ast = parse(code)
        Optimize()(ast)
        self.assertMultiLineEqual(format(ast), format(parse(expected)))

    def test_local_optimization(self):
        code = """
        local a = 1
        local b = 2
        local c = a + b
        """
        expected = """
        local a, b,c
        a = 1
        b = 2
        c = a + b
        """
        self.run_test(code, expected)

    def test_def_only_local_assigns(self):
        code = """
        local a, b
        a = 1
        b = 2
        local c = a + b
        foo(c)
        """
        expected = """
        local a, b, c
        a = 1
        b = 2
        c = a + b
        foo(c)
        """
        self.run_test(code, expected)
