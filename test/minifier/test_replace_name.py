import unittest

from tumfl import format, parse
from tumfl.AST import BinOp, FunctionCall
from tumfl.minifier.util.replace_name import *
from tumfl.minifier.util.replacements import Replacements


class TestReplaceName(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def code_equal(self, node: Block, code: str):
        to_compare = parse(code)
        self.assertMultiLineEqual(format(node), format(to_compare))

    def test_add_alias(self):
        ast = parse("foo()")
        first_func = ast.statements[0]
        assert isinstance(first_func, FunctionCall)
        assert isinstance(first_func.function, Name)
        to_alias = [Replacements([first_func.function], first_func.function)]
        to_alias[0].replacement = "re0"
        add_aliases(ast, to_alias)
        expected = """
        re0 = foo
        foo()
        """
        self.code_equal(ast, expected)

    def test_add_alias_nested(self):
        ast = parse("foo.bar()")
        first_func = ast.statements[0]
        assert isinstance(first_func, FunctionCall)
        assert isinstance(first_func.function, NamedIndex)
        assert isinstance(first_func.function.lhs, Name)
        to_alias = [
            Replacements(
                [first_func.function.variable_name], first_func.function.variable_name
            )
        ]
        to_alias[0].replacement = "re0"
        add_aliases(ast, to_alias)
        expected = """
        re0 = foo.bar
        foo.bar()
        """
        self.code_equal(ast, expected)

    def test_add_alias_deeply_nested(self):
        ast = parse("foo.bar.baz()")
        first_func = ast.statements[0]
        assert isinstance(first_func, FunctionCall)
        assert isinstance(first_func.function, NamedIndex)
        assert isinstance(first_func.function.lhs, NamedIndex)
        assert isinstance(first_func.function.lhs.lhs, Name)
        to_alias = [
            Replacements(
                [first_func.function.variable_name], first_func.function.variable_name
            )
        ]
        to_alias[0].replacement = "re0"
        add_aliases(ast, to_alias)
        expected = """
        re0 = foo.bar.baz
        foo.bar.baz()
        """
        self.code_equal(ast, expected)

    def test_add_alias_deeply_nested_with_second_alias(self):
        ast = parse("foo.bar.baz()")
        first_func = ast.statements[0]
        assert isinstance(first_func, FunctionCall)
        assert isinstance(first_func.function, NamedIndex)
        assert isinstance(first_func.function.lhs, NamedIndex)
        assert isinstance(first_func.function.lhs.lhs, Name)
        to_alias = [
            Replacements(
                [first_func.function.variable_name], first_func.function.variable_name
            ),
            Replacements(
                [first_func.function.lhs.variable_name],
                first_func.function.lhs.variable_name,
            ),
        ]
        to_alias[0].replacement = "re0"
        to_alias[1].replacement = "re1"
        to_alias[0].parent = to_alias[1]
        add_aliases(ast, to_alias)
        expected = """
        re1 = foo.bar
        re0 = foo.bar.baz
        foo.bar.baz()
        """
        self.code_equal(ast, expected)

    def test_add_alias_after(self):
        ast = parse("foo = {} foo.bar()")
        definition = ast.statements[0]
        assert isinstance(definition, Assign)
        definition_target = definition.targets[0]
        assert isinstance(definition_target, Name)
        first_func = ast.statements[1]
        assert isinstance(first_func, FunctionCall)
        assert isinstance(first_func.function, NamedIndex)
        assert isinstance(first_func.function.lhs, Name)
        to_alias = [
            Replacements(
                [first_func.function.variable_name], first_func.function.variable_name
            )
        ]
        to_alias[0].replacement = "re0"
        to_alias[0].after = definition_target
        add_aliases(ast, to_alias)
        expected = """
        foo = {}
        re0 = foo.bar
        foo.bar()
        """
        self.code_equal(ast, expected)

    def test_simple_replace_name(self):
        ast = parse("foo = 1")
        definition = ast.statements[0]
        assert isinstance(definition, Assign)
        definition_target = definition.targets[0]
        assert isinstance(definition_target, Name)
        replace_name(definition_target, "bar")
        self.code_equal(ast, "bar = 1")

    def test_working_method_invocation_replace_name(self):
        ast = parse("foo:bar()")
        definition = ast.statements[0]
        assert isinstance(definition, MethodInvocation)
        assert isinstance(definition.function, Name)
        replace_name(definition.function, "baz")
        self.code_equal(ast, "baz:bar()")

    def test_failing_method_invocation_replace_name(self):
        ast = parse("foo:bar()")
        definition = ast.statements[0]
        assert isinstance(definition, MethodInvocation)
        with self.assertRaises(NotImplementedError):
            replace_name(definition.method, "baz")

    def test_replace_name_in_named_index_outer(self):
        ast = parse("foo.bar()")
        definition = ast.statements[0]
        assert isinstance(definition, FunctionCall)
        assert isinstance(definition.function, NamedIndex)
        assert isinstance(definition.function.lhs, Name)
        replace_name(definition.function.lhs, "baz")
        self.code_equal(ast, "baz.bar()")

    def test_replace_name_in_named_index_inner(self):
        ast = parse("foo.bar()")
        definition = ast.statements[0]
        assert isinstance(definition, FunctionCall)
        assert isinstance(definition.function, NamedIndex)
        replace_name(definition.function.variable_name, "baz")
        self.code_equal(ast, "baz()")

    def test_replace_function_name(self):
        ast = parse("function foo.bar() end")
        definition = ast.statements[0]
        assert isinstance(definition, FunctionDefinition)
        replace_name(definition.names[1], "baz")
        self.code_equal(ast, "function baz() end")

    def test_replace_function_parameter(self):
        ast = parse("function foo.bar(a, b) end")
        definition = ast.statements[0]
        assert isinstance(definition, FunctionDefinition)
        second_parameter = definition.parameters[1]
        assert isinstance(second_parameter, Name)
        replace_name(second_parameter, "baz")
        self.code_equal(
            ast,
            "function foo.bar(a, baz) end",
        )

    def test_replace_function_method(self):
        ast = parse("function foo:bar() end")
        definition = ast.statements[0]
        assert isinstance(definition, FunctionDefinition)
        with self.assertRaises(NotImplementedError):
            assert definition.method_name
            replace_name(definition.method_name, "baz")

    def test_char_sequence(self):
        sequence = char_sequence()
        self.assertEqual(next(sequence), "a")
        for _ in range(24):
            next(sequence)
        self.assertEqual(next(sequence), "z")
        self.assertEqual(next(sequence), "A")
        for _ in range(24):
            next(sequence)
        self.assertEqual(next(sequence), "Z")
        self.assertEqual(next(sequence), "aa")

    def test_full_replace(self):
        ast = parse(
            """
        function foo(a, b)
            return a + b
        end
        foo()
        bar.baz()
        """
        )
        function_definition = ast.statements[0]
        assert isinstance(function_definition, FunctionDefinition)
        first_arg = function_definition.parameters[0]
        assert isinstance(first_arg, Name)
        second_arg = function_definition.parameters[1]
        assert isinstance(second_arg, Name)
        assert function_definition.body.returns
        return_value = function_definition.body.returns[0]
        assert isinstance(return_value, BinOp)
        assert isinstance(return_value.left, Name)
        assert isinstance(return_value.right, Name)
        foo_call = ast.statements[1]
        assert isinstance(foo_call, FunctionCall)
        assert isinstance(foo_call.function, Name)
        bar_call = ast.statements[2]
        assert isinstance(bar_call, FunctionCall)
        assert isinstance(bar_call.function, NamedIndex)
        assert isinstance(bar_call.function.lhs, Name)
        replacements = [
            [
                Replacements([second_arg, return_value.right], None),
            ],
            [
                Replacements([first_arg, return_value.left], None),
            ],
            [
                Replacements([function_definition.names[0], foo_call.function], None),
            ],
            [
                Replacements(
                    [bar_call.function.variable_name], bar_call.function.variable_name
                ),
            ],
        ]
        full_replace(ast, replacements)
        expected = """
        d = bar.baz
        function c(b, a)
            return b + a
        end
        c()
        d()
        """
        self.code_equal(ast, expected)
