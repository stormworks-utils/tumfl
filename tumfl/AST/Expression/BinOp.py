from __future__ import annotations

from enum import Enum

from tumfl.Token import Token

from .Expression import Expression


class BinaryOperand(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIVIDE = "/"
    INTEGER_DIVISION = "//"
    MODULO = "%"
    EXPONENT = "^"
    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "~"
    BIT_SHIFT_LEFT = "<<"
    BIT_SHIFT_RIGHT = ">>"
    CONCAT = ".."
    EQUALS = "=="
    NOT_EQUALS = "~="
    LESS_EQUALS = "<="
    GREATER_EQUALS = ">="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    AND = "and"
    OR = "or"


class BinOp(Expression):
    """Binary Operation, like a + b, 1 and 2 or 4 == b"""

    def __init__(
        self, token: Token, op: BinaryOperand, left: Expression, right: Expression
    ) -> None:
        super().__init__(token, "BinOp")
        self.op: BinaryOperand = op
        self.left: Expression = left
        self.right: Expression = right

    @staticmethod
    def from_token(token: Token, left: Expression, right: Expression) -> BinOp:
        binop: BinaryOperand = BinaryOperand[token.type.name]
        assert binop
        return BinOp(token, binop, left, right)
