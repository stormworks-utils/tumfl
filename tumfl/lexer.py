import sys
from typing import Dict, List, NoReturn, Optional, Tuple, TypedDict

from .error import LexerError
from .Token import Token, TokenType

RESERVED_KEYWORDS: Dict[str, TokenType] = {
    t.value: t
    for t in list(TokenType)
    if t.value.isalpha() and t.value not in ["name", "number", "eof", "string"]
}
SYMBOLS: Dict[str, TokenType] = {
    t.value: t for t in list(TokenType) if not t.value.isalpha()
}
# string.isnumeric works on unicode numbers, too. lua only works on Arabic-Indic digits
NUMBER: List[str] = [str(i) for i in range(10)]
HEX_NUMBER: List[str] = [
    *(chr(i + 65) for i in range(6)),
    *(chr(i + 97) for i in range(6)),
    *NUMBER,
]
LETTER: List[str] = [
    *(chr(i + 65) for i in range(26)),
    *(chr(i + 97) for i in range(26)),
    "_",
]
ALPHANUMERIC: List[str] = [*NUMBER, *LETTER]
ESCAPE_CODES: Dict[str, str] = {
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "\n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

NumberTuple = Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[str]]


class TokenArgs(TypedDict):
    line: int
    column: int
    comment: list[str]


def include_typing(do_include: bool) -> None:
    """
    Change the keywords to include typing

    :param do_include: whether to include typing keywords
    :return: None
    """
    if do_include and "as" not in RESERVED_KEYWORDS:
        RESERVED_KEYWORDS["as"] = TokenType.AS
        RESERVED_KEYWORDS["is"] = TokenType.IS
    elif not do_include and "as" in RESERVED_KEYWORDS:
        RESERVED_KEYWORDS.pop("as")
        RESERVED_KEYWORDS.pop("is")


class Lexer:
    def __init__(
        self, text: str, typed: bool = False, ignore_unicode_errors: bool = False
    ) -> None:
        self.text: str = text
        self.text_len: int = len(self.text)
        self.line: int = 0
        self.column: int = -1
        self.pos: int = -1
        self.newline_warn: int = 0
        self.current_char: Optional[str] = None
        self.last_hint: Optional[Tuple[str, int, int]] = None
        self.comments: list[str] = []
        self.unicode_errors: str = "ignore" if ignore_unicode_errors else "strict"
        self.advance()
        include_typing(typed)

    def error(
        self, message: str, line: Optional[int] = None, column: Optional[int] = None
    ) -> NoReturn:
        current_line: int = line if line is not None else self.line
        current_column = column if column is not None else self.column
        print(f"Error on line {current_line + 1}:", file=sys.stderr)
        print(self.text.split("\n")[current_line], file=sys.stderr)
        print(" " * current_column + "^", file=sys.stderr)
        print(message, file=sys.stderr)
        raise LexerError(message, current_line, current_column)

    def get_token_args(self) -> TokenArgs:
        comment: list[str] = self.comments[:]
        self.comments.clear()
        return {"line": self.line + 1, "column": self.column + 1, "comment": comment}

    def advance(self) -> None:
        """Advance the `pos` pointer"""
        self.pos += 1
        if self.pos < self.text_len:
            self.current_char = self.text[self.pos]
            self.column += 1

            if self.current_char == "\n":
                self.column = -1
                self.line += 1
                # init newline state machine
                self.newline_warn = 1
            elif self.current_char.isspace():
                # third state: space after text after newline
                if self.newline_warn == 2:
                    self.newline_warn = 3
            else:
                # second state: text after newline
                if self.newline_warn == 1:
                    self.newline_warn = 2
                # reset if text after third state
                if self.newline_warn == 3:
                    self.newline_warn = 0
        else:
            self.current_char = None

    def peek(self) -> Optional[str]:
        peek_pos = self.pos + 1
        if peek_pos < self.text_len:
            return self.text[peek_pos]
        return None

    def skip_whitespace(self) -> None:
        while self.current_char and self.current_char.isspace():
            self.advance()

    def get_long_brackets(self) -> str:
        """Returns the inner content of long brackets, or none if there are no long brackets"""
        # check if in the right conditions
        assert self.current_char == "[" and self.peek() in ["=", "["]
        line: int = self.line
        column: int = self.column
        # skip opening bracket
        self.advance()
        # the amount of equals signs in the long string
        equals: int = 0
        # get all equals signs
        while self.current_char == "=":
            equals += 1
            self.advance()
        # check that the opening is not malformed
        if self.current_char != "[":
            self.error("Malformed long bracket")
        self.advance()
        inner_string: str = ""
        # closing_equals is zero on an encountered closing bracket, and will be incremented with each equals sign
        closing_equals: int = -1
        while self.current_char:
            if self.current_char == "]" and closing_equals == equals:
                self.advance()
                return inner_string[: -equals - 1]
            if self.current_char == "=" and closing_equals >= 0:
                closing_equals += 1
            elif self.current_char == "]":
                closing_equals = 0
            else:
                closing_equals = -1
            inner_string += self.current_char
            self.advance()
        self.error("long brackets never closed", line, column)

    def skip_comment(self) -> None:
        """Skip a comment (long or short)"""
        assert self.current_char == "-" and self.peek() == "-"
        self.advance()
        self.advance()
        comment: str = ""
        if self.current_char == "[" and self.peek() in ["[", "="]:
            comment = self.get_long_brackets()
        else:
            while self.current_char and self.current_char != "\n":
                comment += self.current_char
                self.advance()
        self.comments.append(comment)

    def get_number(self) -> NumberTuple:
        """Parses a number into the Number ast node"""
        current_numbers: List[str] = NUMBER
        is_hex: bool = False
        integer_part: Optional[str] = None
        # starts with a digit
        if self.current_char in NUMBER:
            # is a hex number
            if self.current_char == "0" and self.peek() in ["x", "X"]:
                is_hex = True
                current_numbers = HEX_NUMBER
                self.advance()
                self.advance()
            # gather integer digits
            result: str = ""
            while self.current_char in current_numbers:
                result += self.current_char.lower()
                self.advance()
            if result:
                integer_part = result
        if not integer_part:
            self.last_hint = (
                "forgot an integer part of a number",
                self.line,
                self.column,
            )
        # has a fractional part
        fractional_part: Optional[str] = None
        exponent: Optional[str] = None
        float_offset: Optional[str] = None
        if self.current_char == ".":
            self.advance()
            # gather fractional digits
            result = ""
            while self.current_char in current_numbers:
                result += self.current_char.lower()
                self.advance()
            if result:
                fractional_part = result
            else:
                self.last_hint = (
                    "forgot a fractional part after a dot",
                    self.line,
                    self.column,
                )
        # test for a float_offset in hex numbers or an exponent in non-hex numbers
        if (
            is_hex
            and self.current_char in ["p", "P"]
            or not is_hex
            and self.current_char in ["e", "E"]
        ):
            self.advance()
            result = ""
            # take a sign if it exists
            if self.current_char in ["+", "-"]:
                result += self.current_char
                self.advance()
            # gather digits
            while self.current_char in NUMBER:
                result += self.current_char
                self.advance()
            # store in the respective field
            if result and is_hex:
                float_offset = result
            elif result:
                exponent = result
        return is_hex, integer_part, fractional_part, exponent, float_offset

    def get_name(self) -> str:
        assert self.current_char in LETTER
        result: str = ""
        while self.current_char in ALPHANUMERIC:
            result += self.current_char
            self.advance()
        return result

    def _safe_decode(self, base: int) -> str:
        try:
            return bytes((base,)).decode("utf-8", self.unicode_errors)
        except UnicodeDecodeError:
            self.error(
                f"This library can't handle invalid unicode characters, got {base}"
            )

    def _safe_code_point(self, base: int) -> str:
        try:
            return chr(base)
        except ValueError:
            if self.unicode_errors == "strict":
                self.error(f"Invalid unicode codepoint, got {base}")
        return ""

    def get_string(self) -> str:
        assert self.current_char in ["'", '"']
        # character that is needed to close the string
        closing: str = self.current_char
        # whether the next character has been escaped
        escape: bool = False
        self.advance()
        # the result string that will contain the parsed string
        result: str = ""
        # iterate until either the end is reached, or an unescaped closing character is encountered
        while self.current_char and (escape or self.current_char != closing):
            # handle an escaped character
            if escape:
                column: int = self.column
                # handle the skip next whitespace escape sequence
                if self.current_char == "z":
                    self.advance()
                    self.skip_whitespace()
                # handle the hexadecimal character specification case
                elif self.current_char == "x":
                    self.advance()
                    digits: str = self.current_char
                    # needs to have exactly 2 digits
                    if self.current_char not in HEX_NUMBER:
                        self.error("Invalid hex digit", column=column)
                    self.advance()
                    digits += self.current_char
                    if self.current_char not in HEX_NUMBER:
                        self.error("Invalid hex digit", column=column)
                    self.advance()
                    result += self._safe_decode(int(digits, 16))
                elif self.current_char == "u":
                    self.advance()
                    if self.current_char != "{":
                        self.error("Invalid character after \\u, expected {")
                    self.advance()
                    codepoint: str = ""
                    for _ in range(8):
                        codepoint += self.current_char
                        if self.current_char not in HEX_NUMBER:
                            self.error(
                                "Invalid unicode codepoint, expected hexadecimal number"
                            )
                        self.advance()
                        if self.current_char == "}":
                            break
                    else:
                        self.error(
                            "Unicode codepoints can be at most 2^31 - 1, did not close unicode escape"
                        )
                    result += self._safe_code_point(int(codepoint, 16))
                # handle the decimal character specification case
                elif self.current_char in NUMBER:
                    digits = self.current_char
                    self.advance()
                    # may have up to 3 digits
                    if self.current_char in NUMBER:
                        digits += self.current_char
                        self.advance()
                    if self.current_char in NUMBER:
                        digits += self.current_char
                        self.advance()
                    char: int = int(digits)
                    if char > 255:
                        self.error(f"Invalid char with number {char}", column=column)
                    result += self._safe_decode(char)
                else:
                    # handle all simple escape sequences
                    if self.current_char not in ESCAPE_CODES:
                        self.error(
                            f"Invalid escape sequence: \\{self.current_char}",
                            column=column,
                        )
                    result += ESCAPE_CODES[self.current_char]
                    self.advance()
                escape = False
            elif self.current_char == "\\":
                # escape the next character. don't do anything in this loop
                escape = True
                self.advance()
            else:
                # normal characters
                if self.current_char == "\n":
                    self.error("Invalid end of string")
                result += self.current_char
                self.advance()
        # eof before closing character
        if self.current_char != closing:
            self.error("Did not close string")
        self.advance()
        return result

    def get_next_token(self) -> Token:
        # skip prelude
        if self.line == 0 and self.column == 0 and self.current_char == "#":
            while self.current_char and self.current_char != "\n":
                self.advance()
        while self.current_char:
            self.last_hint = None
            # skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # skip comments
            if self.current_char == "-" and self.peek() == "-":
                self.skip_comment()
                continue

            args: TokenArgs = self.get_token_args()

            if self.current_char in LETTER:
                name: str = self.get_name()
                if token_type := RESERVED_KEYWORDS.get(name):
                    return Token(token_type, name, **args)
                return Token(TokenType.NAME, name, **args)

            if (
                self.current_char in NUMBER
                or self.current_char == "."
                and self.peek() in NUMBER
            ):
                number: NumberTuple = self.get_number()
                return Token(TokenType.NUMBER, number, **args)

            if self.current_char in ["'", '"']:
                string: str = self.get_string()
                return Token(TokenType.STRING, string, **args)

            if self.current_char == "[" and self.peek() in ["[", "="]:
                string = self.get_long_brackets()
                return Token(TokenType.STRING, string, **args)

            if self.current_char == "." and self.peek() == ".":
                self.advance()
                self.advance()
                if self.current_char == ".":
                    self.advance()
                    return Token(TokenType.ELLIPSIS, "...", **args)
                return Token(TokenType.CONCAT, "..", **args)

            if peek := self.peek():
                double_character: str = self.current_char + peek
                if token_type := SYMBOLS.get(double_character):
                    self.advance()
                    self.advance()
                    return Token(token_type, double_character, **args)
            char: str = self.current_char
            if token_type := SYMBOLS.get(char):
                self.advance()
                return Token(token_type, char, **args)

            self.error(f"unrecognised character {self.current_char}")
        return Token(TokenType.EOF, "eof", **self.get_token_args())
