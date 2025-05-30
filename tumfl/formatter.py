from __future__ import annotations

import string
from enum import Enum
from typing import Any, Iterator, Literal, Optional, Sequence, Type

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
    # highest number of newline characters before using a multiline string
    NEWLINE_LIMIT: int = 4
    # How big lines may be. Note: there is no guarantee that this will be honored. Use 0 for no limit
    LINE_WIDTH: int = 120
    # Number of lines in a block to add spacers before and after the block. Use 0 to disable
    BLOCK_SPACER: int = 5
    # Keep semicolons
    KEEP_SEMICOLON: bool = False
    # add extra newlines, i.e. before and after functions
    EXTRA_NEWLINES: bool = True


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
    NEWLINE_LIMIT = 1
    LINE_WIDTH = 0
    BLOCK_SPACER = 0
    EXTRA_NEWLINES = False


class Separators(Enum):
    Statement = "stmt"
    Newline = "newline"
    Argument = "arg"
    Space = " "
    Dot = "."
    Indent = "indent"
    DeIndent = "de-indent"
    Block = "block"

    def join(self, to_join: Iterator[Retype]) -> Retype:
        join_list: list[Retype] = list(to_join)
        for i in range(len(join_list) - 1, 0, -1):
            join_list[i:i] = [[self]]
        return [elem for part in join_list for elem in part]

    def __repr__(self) -> str:
        return f"Separators.{self.name}"


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


def unused(_: Any) -> None:
    pass


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
        prefix: str = "-" if comment and comment[0] == "-" else ""
        comment = comment.lstrip("-")
        if force_long or "\n" in comment:
            level: int = self._find_level(comment)
            return [
                f"--{prefix}[{'=' * level}[{comment}]{'=' * level}]",
                Separators.Statement,
            ]
        return [f"--{prefix}{self.s.COMMENT_SEP}{comment}", Separators.Newline]

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
        result: Retype = ["do", Separators.Block, Separators.Indent]
        for statement in node.statements:
            if self.s.INCLUDE_COMMENTS and statement.comment:
                for comment in statement.comment:
                    result += self._format_comment(comment)
            result += self.visit(statement) + [Separators.Statement]
        if node.returns is not None:
            opt_space: tuple[Separators, ...] = (
                (Separators.Space,) if node.returns else ()
            )
            returns: Retype = self._format_args(node.returns)
            result += ["return", *opt_space, *returns, Separators.Statement]
        result += [Separators.DeIndent, "end"]
        return result

    def visit_Boolean(self, node: Boolean) -> Retype:
        return [str(node.value).lower()]

    def visit_Break(self, node: Break) -> Retype:
        unused(node)
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
        result: Retype = ["if", *spaced_test, "then", Separators.Block]
        result += self.visit(node.true)[2:-1]
        current_if: If = node
        while isinstance(current_if.false, If):
            current_if = current_if.false
            spaced_test = [
                Separators.Space,
                *self.visit(current_if.test),
                Separators.Space,
            ]
            result += ["elseif", *spaced_test, "then", Separators.Block]
            result += self.visit(current_if.true)[2:-1]
        if current_if.false:
            result += ["else", Separators.Block]
            result += self.visit(current_if.false)[2:-1]
        result += ["end"]
        return result

    def visit_Index(self, node: Index) -> Retype:
        return [*self._format_var(node.lhs), "[", *self.visit(node.variable_name), "]"]

    def visit_Label(self, node: Label) -> Retype:
        return ["::", *self.visit(node.label_name), "::"]

    def visit_Name(self, node: Name) -> Retype:
        return [node.variable_name]

    def visit_Nil(self, node: Nil) -> Retype:
        unused(node)
        return ["nil"]

    def visit_Number(self, node: Number) -> Retype:
        return [str(node)]

    def visit_Repeat(self, node: Repeat) -> Retype:
        return [
            "repeat",
            Separators.Block,
            *self.visit(node.body)[2:-1],
            "until",
            Separators.Space,
            *self.visit(node.condition),
        ]

    def visit_Semicolon(self, node: Semicolon) -> Retype:
        unused(node)
        return [";"] if self.s.KEEP_SEMICOLON else []

    def visit_String(self, node: String) -> Retype:
        escaped: str = ""
        quote: str = '"'
        contains_unprintable: bool = False
        single_quote_count: int = 0
        double_quote_count: int = 0
        newline_count: int = 0
        for char in node.value:
            if char == "\n":
                newline_count += 1
            elif char == "'":
                single_quote_count += 1
            elif char == '"':
                double_quote_count += 1
            elif not 32 <= ord(char) < 127:
                contains_unprintable = True
        # do not use multiline strings if the number of newlines is too low
        if newline_count > self.s.NEWLINE_LIMIT and not contains_unprintable:
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
                escaped += f"\\{ESCAPE_CHARACTERS[char]}"
            else:
                escaped += f"\\x{ord(char):02x}"
        return [quote + escaped + quote]

    def visit_Table(self, node: Table) -> Retype:
        return ["{", *self._format_args(node.fields), "}"]

    def visit_Vararg(self, node: Vararg) -> Retype:
        unused(node)
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
                or other_node.op.non_commutative()
                and own_precedence == other_node.op.get_precedence()
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
        extra_newline = (Separators.Newline,) if self.s.EXTRA_NEWLINES else ()
        return [
            *extra_newline,
            "function",
            Separators.Space,
            *full_name,
            "(",
            *self._format_args(node.parameters),
            ")",
            *self.visit(node.body)[1:],
            Separators.Block,
            *extra_newline,
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
            Separators.Newline,
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
            Separators.Newline,
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
            if own_token not in (
                Separators.Space,
                Separators.Statement,
                Separators.Block,
            ):
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


def __get_indentation_width(style: Type[FormattingStyle]) -> int:
    return len(style.INDENTATION.replace("\t", "    "))


def __estimate_width(
    indentation: int,
    stream: Retype,
    style: Type[FormattingStyle],
    with_indentation: bool = True,
) -> Optional[int]:
    """
    Estimate the width of a stream

    :param indentation: indentation of the stream
    :param stream: The stream to estimate
    :param style: Formatting style to apply
    :return: None if multiline, estimated width otherwise
    """
    size: int = 0
    if with_indentation:
        size = indentation * __get_indentation_width(style)
    for token in stream:
        match token:
            case Separators.Space | Separators.Dot:
                size += 1
            case Separators.Argument:
                size += len(style.ARGUMENT_SEPARATOR)
            case Separators.Newline | Separators.Statement | Separators.Block:
                return None
            case Separators.Indent | Separators.DeIndent:
                pass
            case literal_string:
                if "\n" in literal_string:
                    return None
                size += len(literal_string)
    return size


def __get_newline_pos(input_string: str, max_pos: int) -> int:
    if len(input_string) < max_pos:
        return len(input_string)
    current_pos: int = max_pos
    while current_pos > 1:
        is_end: bool = current_pos == len(input_string)
        is_allowed: bool = is_end or not input_string[current_pos].isspace()
        is_word_break: bool = not input_string[current_pos - 1].isalnum()
        if is_allowed and is_word_break:
            return current_pos
        current_pos -= 1
    current_pos = max_pos
    while current_pos < len(input_string):
        if not input_string[current_pos].isspace():
            return current_pos
        current_pos += 1
    return len(input_string)


def _string_ident(
    input_string: str, indentation: int, style: Type[FormattingStyle]
) -> Retype:
    start: str = input_string[0]
    assert start in "'\""
    assert input_string[-1] == start
    width = __estimate_width(indentation, [input_string], style)
    if width and width <= style.LINE_WIDTH:
        return [input_string]
    raw_indentation: int = indentation * __get_indentation_width(style) + 2
    result: Retype = []
    while input_string:
        pos = __get_newline_pos(input_string, style.LINE_WIDTH - raw_indentation)
        if pos >= len(input_string) - 2:
            pos = len(input_string)
        result.append(input_string[:pos] + "\\z")
        result.append(Separators.Newline)
        input_string = input_string[pos:]
    # remove last newline
    result.pop()
    last_string = result[-1]
    assert isinstance(last_string, str)
    # remove last \z
    result[-1] = last_string[:-2]
    return result


MATCHING_BRACKETS: dict[str, str] = {"}": "{", "]": "[", ")": "("}


def __inner_indent(
    token_stream: Retype, index: int, indentation: int, style: Type[FormattingStyle]
) -> tuple[int, Retype]:
    opening: str | Separators = token_stream[index]
    assert opening in MATCHING_BRACKETS
    closing: str = MATCHING_BRACKETS[opening]  # type: ignore
    # lua functions don't allow trailing argument separators
    use_trailing: bool = opening != ")"
    components: list[Retype] = []
    current_component: Retype = []
    index -= 1
    while True:
        current_char = token_stream[index]
        if current_char == closing:
            break
        if current_char in MATCHING_BRACKETS:
            index, content = __inner_indent(token_stream, index, indentation + 1, style)
            current_component[0:0] = content
        elif current_char == Separators.Argument:
            components.insert(0, current_component)
            current_component = []
        elif isinstance(current_char, str) and (
            current_char.startswith('"') or current_char.startswith("'")
        ):
            current_component[0:0] = _string_ident(current_char, indentation + 1, style)
        else:
            current_component.insert(0, current_char)
        index -= 1
    if current_component:
        components.insert(0, current_component)
    width: int = 0
    for component in components:
        current_width: Optional[int] = __estimate_width(
            indentation, component, style, with_indentation=False
        )
        if current_width is None:
            width = style.LINE_WIDTH + 1
            break
        width += current_width + len(style.ARGUMENT_SEPARATOR)
    if (
        width + 2 + indentation * __get_indentation_width(style) <= style.LINE_WIDTH
        or len(components) <= 1
    ):
        return index, [closing, *Separators.Argument.join(iter(components)), opening]
    result: Retype = [closing, Separators.Indent, Separators.Newline]
    for component in components:
        result.extend(component)
        result.append(Separators.Argument)
        result.append(Separators.Newline)
    if not use_trailing:
        result.pop(len(result) - 2)
    result.append(Separators.DeIndent)
    result.append(opening)
    return index, result


def indent_brackets(token_stream: Retype, style: Type[FormattingStyle]) -> None:
    indentation: int = 0
    index = len(token_stream) - 1
    while index >= 0:
        token = token_stream[index]
        # iterating backwards
        if token == Separators.DeIndent:
            indentation += 1
        elif token == Separators.Indent:
            indentation -= 1
        elif token in MATCHING_BRACKETS:
            start_index = index
            index, content = __inner_indent(token_stream, index, indentation, style)
            token_stream[index : start_index + 1] = content
        elif isinstance(token, str) and (
            token.startswith('"') or token.startswith("'")
        ):
            token_stream[index : index + 1] = _string_ident(token, indentation, style)
        index -= 1


def __inner_add_spacing(
    token_stream: Retype, index: int, to_add: set[int], style: Type[FormattingStyle]
) -> tuple[int, int]:
    last_statement_idx: Optional[int] = None
    total_line_breaks: int = 0
    current_line_breaks: int = 0
    while index < len(token_stream):
        token = token_stream[index]
        if token == Separators.Indent:
            index, newlines = __inner_add_spacing(
                token_stream, index + 1, to_add, style
            )
            current_line_breaks += newlines
        elif token == Separators.DeIndent:
            return index, total_line_breaks + current_line_breaks
        elif token == Separators.Newline:
            current_line_breaks += 1
        elif isinstance(token, str):
            current_line_breaks += token.count("\n")
        elif token == Separators.Statement:
            total_line_breaks += current_line_breaks + 1
            if (
                current_line_breaks > style.BLOCK_SPACER
                and last_statement_idx is not None
            ):
                to_add.add(last_statement_idx + 1)
                to_add.add(index + 1)
            last_statement_idx = index
            current_line_breaks = 0
        index += 1
    return index, total_line_breaks + current_line_breaks


def add_spacing(token_stream: Retype, style: Type[FormattingStyle]) -> None:
    to_add: set[int] = set()
    __inner_add_spacing(token_stream, 0, to_add, style)
    for i in sorted(to_add, reverse=True):
        token_stream.insert(i, Separators.Newline)


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
            elif token in (Separators.Statement, Separators.Block):
                token_stream[i] = style.STATEMENT_SEPARATOR
            elif token == Separators.Argument:
                if token_stream[i + 1] == Separators.Newline:
                    token_stream[i] = style.ARGUMENT_SEPARATOR.rstrip()
                else:
                    token_stream[i] = style.ARGUMENT_SEPARATOR
            elif token == Separators.Newline:
                token_stream[i] = newline
                i += 1
                while i < len(token_stream) and token_stream[i] == Separators.Newline:
                    token_stream[i] = ""


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
            if token.endswith("\n"):
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


def __remove_orphaned_tokens(token_stream: Retype) -> None:
    for i in range(len(token_stream) - 1, -1, -1):
        token = token_stream[i]
        if token == "":
            token_stream.pop(i)
        elif token == Separators.Statement:
            if not isinstance(token_stream[i - 1], str):
                token_stream.pop(i)
            elif token_stream[i : i + 3] == [
                Separators.Statement,
                Separators.Newline,
                Separators.DeIndent,
            ]:
                token_stream.pop(i)


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
    if style.LINE_WIDTH > 0:
        indent_brackets(token_stream, style)
    if style.BLOCK_SPACER > 0:
        add_spacing(token_stream, style)
    token_stream[0:0] = [f"--{style.COMMENT_SEP}tumfl", Separators.Newline]
    __remove_orphaned_tokens(token_stream)
    resolve_tokens(token_stream, style)
    indent(token_stream, style.INDENTATION)
    end = style.STATEMENT_SEPARATOR
    if style.REMOVE_UNNECESSARY_CHARS:
        end = ""
    formatted = join_tokens(token_stream)
    return "\n".join(line.rstrip() for line in formatted.split("\n")).strip() + end
