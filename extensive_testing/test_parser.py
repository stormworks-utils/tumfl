import sys
import unittest
from pathlib import Path

from tumfl.parser import Parser


class RunLuaTests(unittest.TestCase):
    def test_parser_tests(self) -> None:
        test_dir: Path = Path("lua-tests")
        for file in test_dir.glob("*.lua"):
            print(f"Testing parsing {file}", file=sys.stderr)
            with open(file, encoding="iso-8859-15") as f:
                content: str = f.read()
            parser = Parser(content)
            parser.parse_chunk()
