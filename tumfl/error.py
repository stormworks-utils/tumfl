from __future__ import annotations

from typing import TYPE_CHECKING

from .Token import Token

if TYPE_CHECKING:
    from .parser import Hint


class TumflError(Exception):
    pass


class ParserError(TumflError):
    def __init__(self, message: str, hints: list[Hint], token: Token, full_error: str):
        super().__init__(message)
        self.hints: list[Hint] = hints
        self.token: Token = token
        # Fully rendered error message
        self.full_error: str = full_error


class InvalidDependencyError(TumflError):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token: Token = token


class LexerError(TumflError):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line: int = line
        self.column: int = column


class SemanticError(TumflError):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token: Token = token


class InterpreterError(TumflError):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token: Token = token
