import sys
import unittest
from pathlib import Path

from tumfl.lexer import Lexer, TokenType
from tumfl.parser import Parser


class ExtensiveTesting(unittest.TestCase):
    files: list[tuple[str, str]] = []

    def setUp(self) -> None:
        test_dir: Path = Path("lua-tests")
        for file in test_dir.glob("*.lua"):
            with open(file, encoding="iso-8859-15") as f:
                self.files.append((str(file), f.read()))

    def test_lexer(self) -> None:
        for filename, file_content in self.files:
            print(f"Testing lexing {filename}", file=sys.stderr)
            lex = Lexer(file_content)
            while lex.get_next_token().type != TokenType.EOF:
                ...

    def test_parser(self) -> None:
        for filename, file_content in self.files:
            print(f"Testing parsing {filename}", file=sys.stderr)
            parser = Parser(file_content)
            parser.parse_chunk()
            self.assertEqual(len(parser.context_hints), 0)
            self.assertEqual(parser.current_token.type, TokenType.EOF)
