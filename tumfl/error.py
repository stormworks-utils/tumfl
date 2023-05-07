from __future__ import annotations

from typing import TYPE_CHECKING

from .Token import Token

if TYPE_CHECKING:
    from .parser import Hint


class TumflException(Exception):
    ...


class ParserException(TumflException):
    def __init__(self, message: str, hints: list[Hint], token: Token):
        super().__init__(message)
        self.hints: list[Hint] = hints
        self.token: Token = token


class LexerException(TumflException):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line: int = line
        self.column: int = column
