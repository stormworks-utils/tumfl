from .Token import Token


class TumflException(Exception):
    ...


class ParserException(TumflException):
    def __init__(self, message: str, hints: list[tuple[Token, str, str]], token: Token):
        super().__init__(message)
        self.hints: list[tuple[Token, str, str]] = hints
        self.token: Token = token


class LexerException(TumflException):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line: int = line
        self.column: int = column
