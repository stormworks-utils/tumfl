import unittest
from pathlib import Path

from tumfl.lexer import *


class RunLuaTests(unittest.TestCase):
    def test_lex_tests(self) -> None:
        test_dir: Path = Path("lua-tests")
        for file in test_dir.glob("*.lua"):
            print(f"Testing lexing {file}", file=sys.stderr)
            with open(file, encoding="iso-8859-15") as f:
                content: str = f.read()
            lex = Lexer(content)
            while lex.get_next_token().type != TokenType.EOF:
                ...
