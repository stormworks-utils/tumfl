from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from .lexer import NumberTuple


class TokenType(Enum):
    AND = "and"
    BREAK = "break"
    DO = "do"
    ELSE = "else"
    ELSEIF = "elseif"
    END = "end"
    FALSE = "false"
    FOR = "for"
    FUNCTION = "function"
    GOTO = "goto"
    IF = "if"
    IN = "in"
    LOCAL = "local"
    NIL = "nil"
    NOT = "not"
    OR = "or"
    REPEAT = "repeat"
    RETURN = "return"
    THEN = "then"
    TRUE = "true"
    UNTIL = "until"
    WHILE = "while"
    AS = "as"
    IS = "is"
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIVIDE = "/"
    MODULO = "%"
    EXPONENT = "^"
    HASH = "#"
    EQUALS = "=="
    NOT_EQUALS = "~="
    LESS_EQUALS = "<="
    GREATER_EQUALS = ">="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    ASSIGN = "="
    L_PAREN = "("
    R_PAREN = ")"
    L_CURL = "{"
    R_CURL = "}"
    L_BRACKET = "["
    R_BRACKET = "]"
    SEMICOLON = ";"
    COLON = ":"
    LABEL_BORDER = "::"
    COMMA = ","
    DOT = "."
    CONCAT = ".."
    ELLIPSIS = "..."
    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "~"
    BIT_SHIFT_LEFT = "<<"
    BIT_SHIFT_RIGHT = ">>"
    INTEGER_DIVISION = "//"
    NAME = "name"
    NUMBER = "number"
    STRING = "string"
    EOF = "eof"


class Token:
    def __init__(
        self,
        type: TokenType,
        value: Union[str, bool, NumberTuple],
        line: int,
        column: int,
        comment: Optional[list[str]] = None,
    ) -> None:
        self.type: TokenType = type
        self.value: Union[str, bool, NumberTuple] = value
        self.line: int = line
        self.column: int = column
        self.comment: list[str] = comment or []

    def __hash__(self) -> int:
        return hash((self.type, self.value))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return False

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.line!r}, {self.column!r}, {self.comment!r})"
