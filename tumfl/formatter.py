from __future__ import annotations

import string
from enum import Enum
from typing import Iterator, Optional, Sequence, Type

from .AST import *
from .basic_walker import BasicWalker


class FormattingStyle:
    # pylint: disable=too-few-public-methods

    # Statement separator
    STATEMENT_SEPARATOR: str = "\n"
    # Indentation character
    INDENTATION: str = "\t"
    # Argument separator
    ARGUMENT_SEPARATOR: str = ", "
    # Include comments or omit them
    INCLUDE_COMMENTS: bool = True
    # Separator after --
    COMMENT_SEP: str = " "
    # Use single quotes if this saves on string escapes
    USE_SINGLE_QUOTE: bool = False
    # Use direct table and string calls
    USE_CALL_SHORTHAND: bool = False
    # Remove all characters that are not strictly required
    REMOVE_UNNECESSARY_CHARS: bool = False
    # Add brackets to arithmetic expressions no matter the use
    ADD_ALL_BRACKETS: bool = False
    # Add brackets to arithmetic expressions if the order is potentially confusing
    ADD_CLOSE_BRACKETS: bool = True


class MinifiedStyle(FormattingStyle):
    # pylint: disable=too-few-public-methods

    STATEMENT_SEPARATOR = ";"
    INDENTATION = ""
    ARGUMENT_SEPARATOR = ","
    INCLUDE_COMMENTS = False
    USE_SINGLE_QUOTE = True
    USE_CALL_SHORTHAND = True
    REMOVE_UNNECESSARY_CHARS = True


class Separators(Enum):
    Statement: str = "stmt"
    Newline: str = "newline"
    Argument: str = "arg"
    Space: str = " "
    Dot: str = "."
    Indent: str = "indent"
    DeIndent: str = "de-indent"

    def join(self, to_join: Iterator[Retype]) -> Retype:
        join_list: list[Retype] = list(to_join)
        for i in range(len(join_list) - 1, 0, -1):
            join_list[i:i] = [[self]]
        return [elem for part in join_list for elem in part]


Retype = list[str | Separators]


class Formatter(BasicWalker[Retype]):
    # pylint: disable=too-many-public-methods

    def __init__(self, style: Type[FormattingStyle]):
        self.s: Type[FormattingStyle] = style

    def _format_args(self, arguments: Sequence[ASTNode]) -> Retype:
        return Separators.Argument.join(self.visit(arg) for arg in arguments)

    @staticmethod
    def _find_level(to_check: str) -> int:
        level: int = 0
        while True:
            if f"[{'=' * level}[" not in to_check:
                break
            level += 1
        return level

    def _format_comment(self, comment: str, force_long: bool = False) -> Retype:
        comment = comment.strip()
        if force_long or "\n" in comment:
            level: int = self._find_level(comment)
            return [f"--[{'=' * level}[{comment}]{'=' * level}]"]
        return [f"--{self.s.COMMENT_SEP}{comment}", Separators.Newline]

    def _format_function_args(self, args: Sequence[Expression]) -> Retype:
        if self.s.USE_CALL_SHORTHAND and len(args) == 1:
            if isinstance(args[0], String):
                return self.visit(args[0])
            if isinstance(args[0], Table):
                return self.visit(args[0])
        return ["(", *self._format_args(args), ")"]

    def visit_Assign(self, node: Assign) -> Retype:
        return [
            *self._format_args(node.targets),
            Separators.Space,
            "=",
            Separators.Space,
            *self._format_args(node.expressions),
        ]

    def visit_Block(self, node: Block) -> Retype:
        result: Retype = [Separators.Indent]
        for statement in node.statements:
            if self.s.INCLUDE_COMMENTS and statement.comment:
                for comment in statement.comment:
                    result += self._format_comment(comment)
            result += self.visit(statement) + [Separators.Statement]
        if node.returns:
            returns: Retype = self._format_args(node.returns)
            result += ["return", Separators.Space, *returns, Separators.Statement]
        result.append(Separators.DeIndent)
        return result

    def visit_Boolean(self, node: Boolean) -> Retype:
        return [str(node.value).lower()]

    def visit_Break(self, _node: Break) -> Retype:
        return ["break"]

    def visit_Chunk(self, node: Chunk) -> Retype:
        result: Retype = self.visit_Block(node)
        return [Separators.DeIndent, *result[:-3]]

    def visit_Goto(self, node: Goto) -> Retype:
        return ["goto", Separators.Space, self.visit(node.label_name)]

    def visit_If(self, node: If) -> Retype:
        spaced_test: Retype = [
            Separators.Space,
            *self.visit(node.test),
            Separators.Space,
        ]
        result: Retype = ["if", *spaced_test, "then", Separators.Statement]
        result += self.visit(node.true)
        current_if: If = node
        while isinstance(current_if.false, If):
            current_if = current_if.false
            spaced_test = [
                Separators.Space,
                *self.visit(current_if.test),
                Separators.Space,
            ]
            result += ["elseif", *spaced_test, "then", Separators.Statement]
            result += self.visit(current_if.true)
        if current_if.false:
            result += ["else", Separators.Statement]
            result += self.visit(current_if.false)
        result += ["end"]
        return result

    def visit_Index(self, node: Index) -> Retype:
        return [*self.visit(node.lhs), "[", *self.visit(node.variable_name), "]"]

    def visit_Label(self, node: Label) -> Retype:
        return ["::", self.visit(node.label_name), "::"]

    def visit_Name(self, node: Name) -> Retype:
        return [node.variable_name]

    def visit_Nil(self, _node: Nil) -> Retype:
        return ["nil"]

    def visit_Number(self, node: Number) -> Retype:
        return [str(node)]

    def visit_Repeat(self, node: Repeat) -> Retype:
        return [
            "repeat",
            Separators.Statement,
            *self.visit(node.body),
            "until",
            Separators.Space,
            *self.visit(node.condition),
        ]

    def visit_Semicolon(self, _node: Semicolon) -> Retype:
        return [";"]

    def visit_String(self, node: String) -> Retype:
        if "\n" in node.value:
            level: int = self._find_level(node.value)
            return [f"[{'=' * level}[{node.value}]{'=' * level}]"]
        if self.s.USE_SINGLE_QUOTE and node.value.count("'") < node.value.count('"'):
            return ["'" + node.value.replace('"', '\\"') + "'"]
        return ['"' + node.value.replace("'", "\\'") + '"']

    def visit_Table(self, node: Table) -> Retype:
        return ["{", *self._format_args(node.fields), "}"]

    def visit_Vararg(self, _node: Vararg) -> Retype:
        return ["..."]

    def visit_While(self, node: While) -> Retype:
        return [
            "while",
            Separators.Space,
            *self.visit(node.condition),
            Separators.Space,
            "do",
            Separators.Statement,
            *self.visit(node.body),
            "end",
        ]

    def _need_brackets(
        self, own_node: BinOp, other_node: Expression, care_unop: bool
    ) -> bool:
        own_precedence: int = own_node.op.get_precedence()
        close_precedence: int = own_precedence + (
            1 if self.s.ADD_CLOSE_BRACKETS else -1
        )
        return (
            self.s.ADD_ALL_BRACKETS
            or isinstance(other_node, BinOp)
            and (
                other_node.op.get_precedence() < own_precedence
                or other_node.op.get_precedence() == close_precedence
            )
            or (care_unop or self.s.ADD_CLOSE_BRACKETS)
            and isinstance(other_node, UnOp)
            and (10 < own_precedence or 10 == close_precedence)
        )

    def visit_BinOp(self, node: BinOp) -> Retype:
        result: Retype = []
        if self._need_brackets(node, node.left, True):
            result += ["(", *self.visit(node.left), ")"]
        else:
            result += self.visit(node.left)
        result += [Separators.Space, node.op.value, Separators.Space]
        if self._need_brackets(node, node.right, False):
            result += ["(", *self.visit(node.right), ")"]
        else:
            result += self.visit(node.right)
        return result

    def visit_FunctionCall(self, node: FunctionCall) -> Retype:
        return self.visit(node.function) + self._format_function_args(node.arguments)

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> Retype:
        return [
            "function",
            Separators.Space,
            *Separators.Dot.join(self.visit(name) for name in node.names),
            "(",
            *self._format_args(node.parameters),
            ")",
            Separators.Statement,
            *self.visit(node.body),
            "end",
            Separators.Statement,
        ]

    def visit_IterativeFor(self, node: IterativeFor) -> Retype:
        return [
            "for",
            Separators.Space,
            *self._format_args(node.namelist),
            Separators.Space,
            "in",
            Separators.Space,
            *self._format_args(node.explist),
            Separators.Space,
            "do",
            Separators.Statement,
            *self.visit(node.body),
            "end",
        ]

    def visit_LocalAssign(self, node: LocalAssign) -> Retype:
        result: Retype = ["local", Separators.Space]
        result += Separators.Argument.join([str(arg)] for arg in node.variable_names)
        if node.expressions:
            result += [Separators.Space, "=", Separators.Space]
            result += self._format_args(node.expressions)
        return result

    def visit_MethodInvocation(self, node: MethodInvocation) -> Retype:
        return [
            *self.visit(node.function),
            ":",
            *self.visit(node.method),
            *self._format_function_args(node.arguments),
        ]

    def visit_NamedIndex(self, node: NamedIndex) -> Retype:
        return [*self.visit(node.lhs), ".", *self.visit(node.variable_name)]

    def visit_NumericFor(self, node: NumericFor) -> Retype:
        spaced_name: Retype = [
            Separators.Space,
            self.visit(node.variable_name),
            Separators.Space,
        ]
        result: Retype = ["for", *spaced_name, "=", Separators.Space]
        result += self.visit(node.start)
        result += [",", Separators.Space, *self.visit(node.stop)]
        if node.step:
            result += [",", Separators.Space, *self.visit(node.step)]
        result += [Separators.Space, "do", Separators.Statement]
        result += self.visit(node.body)
        result += ["end"]
        return result

    def visit_UnOp(self, node: UnOp) -> Retype:
        result: Retype = [node.op.value]
        if (
            self.s.ADD_ALL_BRACKETS
            or isinstance(node.right, BinOp)
            and node.right.op != BinaryOperand.EXPONENT
        ):
            result += ["(", *self.visit(node.right), ")"]
        elif isinstance(node.right, UnOp) or node.op == UnaryOperand.NOT:
            result += [Separators.Space, *self.visit(node.right)]
        else:
            result += self.visit(node.right)
        return result

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> Retype:
        return self.visit(node.function) + self._format_function_args(node.arguments)

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> Retype:
        return [
            "function",
            Separators.Space,
            "(",
            *self._format_args(node.parameters),
            ")",
            Separators.Statement,
            *self.visit(node.body),
            "end",
        ]

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> Retype:
        return [
            *self.visit(node.function),
            ":",
            *self.visit(node.method),
            *self._format_function_args(node.arguments),
        ]

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> Retype:
        return [
            "local",
            "function",
            Separators.Space,
            *self.visit(node.function_name),
            "(",
            *self._format_args(node.parameters),
            ")",
            Separators.Statement,
            *self.visit(node.body),
            "end",
            Separators.Statement,
        ]

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> Retype:
        return [
            "[",
            *self.visit(node.at),
            "]",
            Separators.Space,
            "=",
            Separators.Space,
            *self.visit(node.value),
        ]

    def visit_NamedTableField(self, node: NamedTableField) -> Retype:
        return [
            *self.visit(node.field_name),
            Separators.Space,
            "=",
            Separators.Space,
            *self.visit(node.value),
        ]

    def visit_NumberedTableField(self, node: NumberedTableField) -> Retype:
        return self.visit(node.value)


def _sep_required(first: str, second: str) -> bool:
    return (
        first in string.ascii_letters
        and second in string.ascii_letters
        or first in string.digits
        and second in string.ascii_letters
        or first in string.ascii_letters
        and second in string.digits
        or first == "-"
        and second == "-"
    )


def _search_token(start_idx: int, direction: int, tokens: Retype) -> str | Separators:
    while isinstance(token := tokens[start_idx], Separators) and token in (
        Separators.Indent,
        Separators.DeIndent,
    ):
        start_idx += direction
    return token


def _remove_separators(token_stream: Retype) -> None:
    token_stream.append("/")
    for i in range(len(token_stream) - 2, 0, -1):
        if isinstance(own_token := token_stream[i], Separators):
            if own_token not in (Separators.Space, Separators.Statement):
                continue
            previous_token = _search_token(i - 1, -1, token_stream)
            next_token = _search_token(i + 1, 1, token_stream)
            if (
                isinstance(previous_token, Separators)
                or isinstance(next_token, Separators)
                or not _sep_required(previous_token[-1], next_token[0])
            ):
                token_stream.pop(i)
    token_stream.pop()


def _resolve_tokens(token_stream: Retype, style: Type[FormattingStyle]) -> None:
    newline: str = (
        style.STATEMENT_SEPARATOR if "\n" in style.STATEMENT_SEPARATOR else "\n"
    )
    for i, token in enumerate(token_stream):
        if isinstance(token, Separators):
            if token == Separators.Space:
                token_stream[i] = " "
            elif token == Separators.Dot:
                token_stream[i] = "."
            elif token == Separators.Statement:
                token_stream[i] = style.STATEMENT_SEPARATOR
            elif token == Separators.Argument:
                token_stream[i] = style.ARGUMENT_SEPARATOR
            elif token == Separators.Newline:
                token_stream[i] = newline


def _indent(token_stream: Retype, indentation_str: str) -> None:
    indentation_level: int = 0
    indentation_dirty: bool = False
    for i, token in enumerate(token_stream):
        if isinstance(token, Separators):
            assert token in (Separators.Indent, Separators.DeIndent)
            if token == Separators.Indent:
                indentation_level += 1
            else:
                indentation_level -= 1
        else:
            if indentation_dirty:
                token_stream[i] = indentation_level * indentation_str + token
                indentation_dirty = False
            if "\n" in token:
                indentation_dirty = True
    assert indentation_level == 0


def _join_tokens(token_stream: Retype) -> str:
    result: str = ""
    for token in token_stream:
        if isinstance(token, str):
            result += token
    return result


def format(ast: ASTNode, style: Optional[Type[FormattingStyle]] = None) -> str:
    style = style or FormattingStyle
    formatter: Formatter = Formatter(style)
    token_stream: Retype = formatter.visit(ast)
    if style.REMOVE_UNNECESSARY_CHARS:
        _remove_separators(token_stream)
    token_stream[0:0] = ["--tumfl", Separators.Newline]
    _resolve_tokens(token_stream, style)
    _indent(token_stream, style.INDENTATION)
    return _join_tokens(token_stream)
