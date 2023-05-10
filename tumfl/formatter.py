from __future__ import annotations

import string
from enum import Enum
from typing import Iterator, Literal, Optional, Sequence, Type

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
    # Add a space around `=` in table constructors
    SPACE_IN_TABLE: bool = True


class MinifiedStyle(FormattingStyle):
    # pylint: disable=too-few-public-methods

    STATEMENT_SEPARATOR = ";"
    INDENTATION = ""
    ARGUMENT_SEPARATOR = ","
    INCLUDE_COMMENTS = False
    COMMENT_SEP = ""
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
ESCAPE_CHARACTERS: dict[str, str] = {
    "\a": "a",
    "\b": "b",
    "\f": "f",
    "\n": "n",
    "\r": "r",
    "\t": "t",
    "\v": "v",
}


class Formatter(BasicWalker[Retype]):
    # pylint: disable=too-many-public-methods

    def __init__(self, style: Type[FormattingStyle]):
        self.s: Type[FormattingStyle] = style

    def _format_args(self, arguments: Sequence[ASTNode]) -> Retype:
        return Separators.Argument.join(self.visit(arg) for arg in arguments)

    @staticmethod
    def _find_level(to_check: str) -> int:
        level: int = 0
        if to_check.endswith("]"):
            level = 1
        while True:
            if (
                f"[{'=' * level}[" not in to_check
                and f"]{'=' * level}]" not in to_check
            ):
                break
            level += 1
        return level

    def _format_comment(self, comment: str, force_long: bool = False) -> Retype:
        comment = comment.strip()
        if force_long or "\n" in comment:
            level: int = self._find_level(comment)
            return [f"--[{'=' * level}[{comment}]{'=' * level}]", Separators.Statement]
        return [f"--{self.s.COMMENT_SEP}{comment}", Separators.Newline]

    def _format_function_args(self, args: Sequence[Expression]) -> Retype:
        if self.s.USE_CALL_SHORTHAND and len(args) == 1:
            if isinstance(args[0], String):
                return self.visit(args[0])
            if isinstance(args[0], Table):
                return self.visit(args[0])
        return ["(", *self._format_args(args), ")"]

    def _format_var(self, var: Expression) -> Retype:
        if isinstance(
            var, (Name, Index, NamedIndex, ExpFunctionCall, ExpMethodInvocation)
        ):
            return self.visit(var)
        return ["(", *self.visit(var), ")"]

    def visit_Assign(self, node: Assign) -> Retype:
        targets: list[Retype] = [self._format_var(var) for var in node.targets]
        return [
            *Separators.Argument.join(iter(targets)),
            Separators.Space,
            "=",
            Separators.Space,
            *self._format_args(node.expressions),
        ]

    def visit_Block(self, node: Block) -> Retype:
        result: Retype = ["do", Separators.Statement, Separators.Indent]
        for statement in node.statements:
            if self.s.INCLUDE_COMMENTS and statement.comment:
                for comment in statement.comment:
                    result += self._format_comment(comment)
            result += self.visit(statement) + [Separators.Statement]
        if node.returns:
            returns: Retype = self._format_args(node.returns)
            result += ["return", Separators.Space, *returns, Separators.Statement]
        result += [Separators.DeIndent, "end"]
        return result

    def visit_Boolean(self, node: Boolean) -> Retype:
        return [str(node.value).lower()]

    def visit_Break(self, _node: Break) -> Retype:
        return ["break"]

    def visit_Chunk(self, node: Chunk) -> Retype:
        result: Retype = self.visit_Block(node)
        return result[3:-3]

    def visit_Goto(self, node: Goto) -> Retype:
        return ["goto", Separators.Space, *self.visit(node.label_name)]

    def visit_If(self, node: If) -> Retype:
        spaced_test: Retype = [
            Separators.Space,
            *self.visit(node.test),
            Separators.Space,
        ]
        result: Retype = ["if", *spaced_test, "then", Separators.Statement]
        result += self.visit(node.true)[2:-1]
        current_if: If = node
        while isinstance(current_if.false, If):
            current_if = current_if.false
            spaced_test = [
                Separators.Space,
                *self.visit(current_if.test),
                Separators.Space,
            ]
            result += ["elseif", *spaced_test, "then", Separators.Statement]
            result += self.visit(current_if.true)[2:-1]
        if current_if.false:
            result += ["else", Separators.Statement]
            result += self.visit(current_if.false)[2:-1]
        result += ["end"]
        return result

    def visit_Index(self, node: Index) -> Retype:
        return [*self._format_var(node.lhs), "[", *self.visit(node.variable_name), "]"]

    def visit_Label(self, node: Label) -> Retype:
        return ["::", *self.visit(node.label_name), "::"]

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
            *self.visit(node.body)[2:-1],
            "until",
            Separators.Space,
            *self.visit(node.condition),
        ]

    def visit_Semicolon(self, _node: Semicolon) -> Retype:
        return [";"]

    def visit_String(self, node: String) -> Retype:
        escaped: str = ""
        quote: str = '"'
        contains_newline: bool = False
        contains_unprintable: bool = False
        single_quote_count: int = 0
        double_quote_count: int = 0
        for char in node.value:
            if char == "\n":
                contains_newline = True
            elif char == "'":
                single_quote_count += 1
            elif char == '"':
                double_quote_count += 1
            elif not 32 <= ord(char) < 127:
                contains_unprintable = True
        if contains_newline and not contains_unprintable:
            level: int = self._find_level(node.value)
            return [f"[{'=' * level}[{node.value}]{'=' * level}]"]
        if self.s.USE_SINGLE_QUOTE and single_quote_count < double_quote_count:
            quote = "'"
        for char in node.value:
            if char in (quote, "\\"):
                escaped += f"\\{char}"
            elif 32 <= ord(char) < 127:
                escaped += char
            elif char in ESCAPE_CHARACTERS:
                if quote == "" and char == "\n":
                    escaped += "\n"
                else:
                    escaped += f"\\{ESCAPE_CHARACTERS[char]}"
            else:
                escaped += f"\\x{ord(char):02x}"
        return [quote + escaped + quote]

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
            *self.visit(node.body),
        ]

    def _need_brackets(
        self, own_node: BinOp, other_node: Expression, care_unop: bool
    ) -> bool:
        own_precedence: int = own_node.op.get_precedence()
        return (
            self.s.ADD_ALL_BRACKETS
            or isinstance(other_node, BinOp)
            and (
                own_precedence > other_node.op.get_precedence()
                or self.s.ADD_CLOSE_BRACKETS
                and other_node.op in own_node.op.get_optional_brackets()
            )
            or (care_unop or self.s.ADD_CLOSE_BRACKETS)
            and isinstance(other_node, UnOp)
            and (
                own_precedence > 10 or self.s.ADD_CLOSE_BRACKETS and own_precedence >= 9
            )
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
        return self._format_var(node.function) + self._format_function_args(
            node.arguments
        )

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> Retype:
        full_name: Retype = Separators.Dot.join(self.visit(name) for name in node.names)
        if node.method_name:
            full_name += [":", *self.visit(node.method_name)]
        return [
            "function",
            Separators.Space,
            *full_name,
            "(",
            *self._format_args(node.parameters),
            ")",
            *self.visit(node.body)[1:],
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
            *self.visit(node.body),
        ]

    def visit_LocalAssign(self, node: LocalAssign) -> Retype:
        result: Retype = ["local", Separators.Space]
        names: list[Retype] = []
        for name in node.variable_names:
            if name.attribute:
                names.append(
                    [str(name.name), Separators.Space, "<", str(name.attribute), ">"]
                )
            else:
                names.append([str(name.name)])
        result += Separators.Argument.join(iter(names))
        if node.expressions:
            result += [Separators.Space, "=", Separators.Space]
            result += self._format_args(node.expressions)
        return result

    def visit_MethodInvocation(self, node: MethodInvocation) -> Retype:
        return [
            *self._format_var(node.function),
            ":",
            *self.visit(node.method),
            *self._format_function_args(node.arguments),
        ]

    def visit_NamedIndex(self, node: NamedIndex) -> Retype:
        return [
            *self._format_var(node.lhs),
            Separators.Dot,
            *self.visit(node.variable_name),
        ]

    def visit_NumericFor(self, node: NumericFor) -> Retype:
        spaced_name: Retype = [
            Separators.Space,
            *self.visit(node.variable_name),
            Separators.Space,
        ]
        result: Retype = ["for", *spaced_name, "=", Separators.Space]
        result += self.visit(node.start)
        result += [Separators.Argument, *self.visit(node.stop)]
        if node.step:
            result += [Separators.Argument, *self.visit(node.step)]
        result.append(Separators.Space)
        result += self.visit(node.body)
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
        return self._format_var(node.function) + self._format_function_args(
            node.arguments
        )

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> Retype:
        return [
            "function",
            Separators.Space,
            "(",
            *self._format_args(node.parameters),
            ")",
            *self.visit(node.body)[1:],
        ]

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> Retype:
        return [
            *self._format_var(node.function),
            ":",
            *self.visit(node.method),
            *self._format_function_args(node.arguments),
        ]

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> Retype:
        return [
            "local",
            Separators.Space,
            "function",
            Separators.Space,
            *self.visit(node.function_name),
            "(",
            *self._format_args(node.parameters),
            ")",
            *self.visit(node.body)[1:],
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


def sep_required(first: str, second: str) -> bool:
    """
    Returns, whether a separator is strictly necessary between 2 tokens

    :param first: last character of first token
    :param second: first character of second token
    :return: if the token is required
    """
    return (
        first in string.ascii_letters + string.digits
        and second in string.ascii_letters + string.digits
        or first == "-"
        and second == "-"
    )


def search_token(
    start_idx: int, direction: Literal[1, -1], tokens: Retype
) -> str | Separators:
    """
    Search for a non indent/de-indent token.

    :param start_idx: the first index to search
    :param direction: in what direction to search, 1 for forwards and -1 for backwards
    :param tokens: the token stream
    :return: the closest non-indent token
    """
    while isinstance(token := tokens[start_idx], Separators) and token in (
        Separators.Indent,
        Separators.DeIndent,
    ):
        start_idx += direction
    return token


def remove_separators(token_stream: Retype) -> None:
    """
    Remove all seperator tokens that are not strictly necessary.

    :param token_stream: The token stream to filter. Removal happens in-place
    :return: None
    """
    # Add a dummy token so that there is definitely a valid final token to look for
    token_stream.append("/")
    for i in range(len(token_stream) - 2, 0, -1):
        if isinstance(own_token := token_stream[i], Separators):
            if own_token not in (Separators.Space, Separators.Statement):
                continue
            previous_token = search_token(i - 1, -1, token_stream)
            next_token = search_token(i + 1, 1, token_stream)
            if (
                isinstance(previous_token, Separators)
                or isinstance(next_token, Separators)
                or not sep_required(previous_token[-1], next_token[0])
            ):
                token_stream.pop(i)
    # Remove the dummy token again
    token_stream.pop()


def resolve_tokens(token_stream: Retype, style: Type[FormattingStyle]) -> None:
    """
    Resolves all tokens except for Indent and DeIndent to strings.

    :param token_stream: the token stream to resolve. Resolving happens in-place
    :param style: The style object
    :return: None
    """
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


def indent(token_stream: Retype, indentation_str: str) -> None:
    """
    Indent the token stream, adding indentation_str once per indentation level in front of existing tokens.

    :param token_stream: the token stream to indent. Indentation happens in-place.
    :param indentation_str: the string to use for indenting
    :return: None
    """
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


def join_tokens(token_stream: Retype) -> str:
    """
    Join all tokens into a string, ignoring all remaining Separators.

    :param token_stream: The token stream to join
    :return: The joined string
    """
    result: str = ""
    for token in token_stream:
        if isinstance(token, str):
            result += token
    return result


def format(ast: ASTNode, style: Optional[Type[FormattingStyle]] = None) -> str:
    """
    Format an ast tree according to the style class.

    :param ast: The AST Node to format, usually a chunk
    :param style: Optional style definition
    :return: Formatted lua
    """
    style = style or FormattingStyle
    formatter: Formatter = Formatter(style)
    token_stream: Retype = formatter.visit(ast)
    if style.REMOVE_UNNECESSARY_CHARS:
        remove_separators(token_stream)
    token_stream[0:0] = [f"--{style.COMMENT_SEP}tumfl", Separators.Newline]
    resolve_tokens(token_stream, style)
    indent(token_stream, style.INDENTATION)
    return join_tokens(token_stream)
