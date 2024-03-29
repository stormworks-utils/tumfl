import sys
import unittest
from pathlib import Path

from tumfl.formatter import format
from tumfl.lexer import Lexer, TokenType
from tumfl.parser import Parser


class ExtensiveTesting(unittest.TestCase):
    files: list[tuple[str, str]] = []
    # Ignored due to invalid codepoints
    ignored_files: list[str] = []

    def setUp(self) -> None:
        test_dir: Path = Path("lua-tests")
        if self.files:
            return
        for file in test_dir.glob("*.lua"):
            if file.name in self.ignored_files:
                continue
            with open(file, encoding="iso-8859-15") as f:
                self.files.append((str(file), f.read()))

    def test_lexer(self) -> None:
        for filename, file_content in self.files:
            print(f"Testing lexing {filename}", file=sys.stderr)
            lex = Lexer(file_content, ignore_unicode_errors=True)
            while lex.get_next_token().type != TokenType.EOF:
                ...

    def test_parser(self) -> None:
        for filename, file_content in self.files:
            print(f"Testing parsing {filename}", file=sys.stderr)
            parser = Parser(file_content, ignore_unicode_errors=True)
            parser.parse_chunk()
            self.assertEqual(len(parser.context_hints), 0)
            self.assertEqual(parser.current_token.type, TokenType.EOF)

    def _test_formatter(self) -> None:
        for filename, file_content in self.files:
            print(f"Testing formatting {filename}", file=sys.stderr)
            chunk = Parser(file_content, ignore_unicode_errors=True).parse_chunk()
            formatted = format(chunk)
            new_chunk = Parser(formatted, ignore_unicode_errors=True).parse_chunk()
            self.assertEqual(chunk, new_chunk)
