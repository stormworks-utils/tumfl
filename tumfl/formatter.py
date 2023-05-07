from __future__ import annotations

import string
from typing import Optional, Sequence, Type

from .AST import *
from .basic_walker import BasicWalker


class FormattingStyle:
    # Statement separator
    STMT_SEP: str = "\n"
    # Indentation character
    INDENT: str = "\t"
    # Argument separator
    ARG_SEP: str = ", "
    # Optional space
    SP: str = " "
    # Include comments or omit them
    INCLUDE_COMMENTS: bool = True
    # Separator after --
    COMMENT_SEP: str = " "
    # Use single quotes if this saves on string escapes
    USE_SINGLE_QUOTE: bool = False
    # Use direct table and string calls
    USE_CALL_SHORTHAND: bool = False


class MinifiedStyle(FormattingStyle):
    STMT_SEP = ";"
    INDENT = ""
    ARG_SEP = ","
    SP = ""
    INCLUDE_COMMENTS = False
    USE_SINGLE_QUOTE = True
    USE_CALL_SHORTHAND = True


class Formatter(BasicWalker[str]):
    def __init__(self, style: Optional[Type[FormattingStyle]] = None):
        self.s: Type[FormattingStyle] = style or FormattingStyle
        self.indentation: int = 0

    def _indent(self, to_indent: str) -> str:
        return self.s.INDENT * self.indentation + to_indent

    def _format_args(self, arguments: Sequence[ASTNode]) -> str:
        return self.s.ARG_SEP.join(self.visit(arg) for arg in arguments)

    @staticmethod
    def _find_level(string: str) -> int:
        level: int = 0
        while True:
            if f"[{'=' * level}[" not in string:
                break
            level += 1
        return level

    def _format_comment(self, comment: str, force_long: bool = False) -> str:
        comment = comment.strip()
        if force_long or "\n" in comment:
            level: int = self._find_level(comment)
            return f"--[{'=' * level}[{comment}]{'=' * level}]"
        newline: str = self.s.STMT_SEP if "\n" in self.s.STMT_SEP else "\n"
        return f"--{self.s.COMMENT_SEP}{comment}{newline}"

    def _format_function_args(self, args: Sequence[Expression]) -> str:
        if self.s.USE_CALL_SHORTHAND and len(args) == 1:
            if isinstance(args[0], String):
                return self.visit(args[0])
            if isinstance(args[0], Table):
                return self.visit(args[0])
        return f"({self._format_args(args)})"

    def visit_Assign(self, node: Assign) -> str:
        targets: str = self._format_args(node.targets)
        expressions: str = self._format_args(node.expressions)
        return f"{targets}{self.s.SP}={self.s.SP}{expressions}"

    def visit_Block(self, node: Block) -> str:
        self.indentation += 1
        result: str = ""
        for statement in node.statements:
            if self.s.INCLUDE_COMMENTS and statement.comment:
                for comment in node.comment:
                    result += self._indent(self._format_comment(comment))
            result += self._indent(self.visit(statement)) + self.s.STMT_SEP
        if node.returns:
            returns: str = self._format_args(node.returns)
            result += self._indent(f"return {returns}{self.s.STMT_SEP}")
        self.indentation -= 1
        return result

    def visit_Boolean(self, node: Boolean) -> str:
        return str(node.value).lower()

    def visit_Break(self, node: Break) -> str:
        return "break"

    def visit_Chunk(self, node: Chunk) -> str:
        self.indentation -= 1
        result: str = self.visit_Block(node)
        self.indentation += 1
        return result.removesuffix("\n\n")

    def visit_Goto(self, node: Goto) -> str:
        return f"goto {node.label_name}"

    def visit_If(self, node: If) -> str:
        result: str = f"if {self.visit(node.test)} then{self.s.STMT_SEP}"
        result += self.visit(node.true)
        current_if: If = node
        while isinstance(current_if.false, If):
            current_if = current_if.false
            result += self._indent(
                f"elseif {self.visit(current_if.test)} then{self.s.STMT_SEP}"
            )
            result += self.visit(current_if.true)
        if current_if.false:
            result += self._indent(f"else{self.s.STMT_SEP}")
            result += self.visit(current_if.false)
        result += self._indent("end")
        return result

    def visit_Index(self, node: Index) -> str:
        return f"{self.visit(node.lhs)}[{self.visit(node.variable_name)}]"

    def visit_Label(self, node: Label) -> str:
        return f"::{node.label_name}::"

    def visit_Name(self, node: Name) -> str:
        return node.variable_name

    def visit_Nil(self, node: Nil) -> str:
        return "nil"

    def visit_Number(self, node: Number) -> str:
        return str(node)

    def visit_Repeat(self, node: Repeat) -> str:
        result: str = f"repeat{self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent(f"until {self.visit(node.condition)}")
        return result

    def visit_Semicolon(self, node: Semicolon) -> str:
        return ";"

    def visit_String(self, node: String) -> str:
        if "\n" in node.value:
            level: int = self._find_level(node.value)
            return f"[{'=' * level}[{node.value}]{'=' * level}]"
        if self.s.USE_SINGLE_QUOTE and node.value.count("'") < node.value.count('"'):
            return "'" + node.value.replace('"', '\\"') + "'"
        return '"' + node.value.replace("'", "\\'") + '"'

    def visit_Table(self, node: Table) -> str:
        return f"{{{self._format_args(node.fields)}}}"

    def visit_Vararg(self, node: Vararg) -> str:
        return "..."

    def visit_While(self, node: While) -> str:
        result: str = f"while {self.visit(node.condition)} do{self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent("end")
        return result

    def visit_BinOp(self, node: BinOp) -> str:
        # TODO: brackets
        return f"{self.visit(node.left)}{self.s.SP}{node.op.value}{self.s.SP}{self.visit(node.right)}"

    def visit_FunctionCall(self, node: FunctionCall) -> str:
        return self.visit(node.function) + self._format_function_args(node.arguments)

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> str:
        names: str = ".".join(self.visit(name) for name in node.names)
        arguments: str = self._format_args(node.parameters)
        result: str = f"function {names}({arguments}){self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent(f"end{self.s.STMT_SEP}")
        return result

    def visit_IterativeFor(self, node: IterativeFor) -> str:
        names: str = self._format_args(node.namelist)
        expressions: str = self._format_args(node.explist)
        result: str = f"for {names} in {expressions} do{self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent("end")
        return result

    def visit_LocalAssign(self, node: LocalAssign) -> str:
        result: str = "local "
        result += self.s.ARG_SEP.join(str(arg) for arg in node.variable_names)
        if node.expressions:
            result += f"{self.s.SP}={self.s.SP}"
            result += self._format_args(node.expressions)
        return result

    def visit_MethodInvocation(self, node: MethodInvocation) -> str:
        arguments: str = self._format_function_args(node.arguments)
        return f"{self.visit(node.function)}:{node.method}{arguments}"

    def visit_NamedIndex(self, node: NamedIndex) -> str:
        return f"{self.visit(node.lhs)}.{node.variable_name}"

    def visit_NumericFor(self, node: NumericFor) -> str:
        result: str = f"for {node.variable_name}{self.s.SP}={self.s.SP}"
        result += self.visit(node.start)
        result += f",{self.s.SP}{self.visit(node.stop)}"
        if node.step:
            result += f",{self.s.SP}{self.visit(node.step)}"
        result += f" do{self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent("end")
        return result

    def visit_UnOp(self, node: UnOp) -> str:
        safety_space: str = ""
        right_text: str = self.visit(node.right)
        if node.op == UnaryOperand.MINUS and right_text.startswith("-"):
            safety_space = " "
        if node.op == UnaryOperand.NOT and right_text[0] in string.ascii_letters:
            safety_space = " "
        return f"{node.op.value}{safety_space}{self.visit(node.right)}"

    def visit_ExpFunctionCall(self, node: ExpFunctionCall) -> str:
        return self.visit(node.function) + self._format_function_args(node.arguments)

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> str:
        arguments: str = self._format_args(node.parameters)
        result: str = f"function ({arguments}){self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent("end")
        return result

    def visit_ExpMethodInvocation(self, node: ExpMethodInvocation) -> str:
        arguments: str = self._format_function_args(node.arguments)
        return f"{self.visit(node.function)}:{node.method}{arguments}"

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> str:
        arguments: str = self._format_args(node.parameters)
        result: str = f"local function {node.name}({arguments}){self.s.STMT_SEP}"
        result += self.visit(node.body)
        result += self._indent(f"end{self.s.STMT_SEP}")
        return result

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> str:
        return f"[{self.visit(node.at)}]{self.s.SP}={self.s.SP}{self.visit(node.value)}"

    def visit_NamedTableField(self, node: NamedTableField) -> str:
        return f"{node.field_name}{self.s.SP}={self.s.SP}{self.visit(node.value)}"

    def visit_NumberedTableField(self, node: NumberedTableField) -> str:
        return self.visit(node.value)


def format(ast: ASTNode, style: Optional[Type[FormattingStyle]] = None) -> str:
    formatter: Formatter = Formatter(style)
    return formatter.visit(ast)
