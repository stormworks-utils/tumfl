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

    def get_precedence(self) -> int:
        if self == BinaryOperand.OR:
            return 0
        if self == BinaryOperand.AND:
            return 1
        if self in (
            BinaryOperand.EQUALS,
            BinaryOperand.NOT_EQUALS,
            BinaryOperand.LESS_EQUALS,
            BinaryOperand.GREATER_EQUALS,
            BinaryOperand.LESS_THAN,
            BinaryOperand.GREATER_THAN,
        ):
            return 2
        if self == BinaryOperand.BIT_OR:
            return 3
        if self == BinaryOperand.BIT_XOR:
            return 4
        if self == BinaryOperand.BIT_AND:
            return 5
        if self in (BinaryOperand.BIT_SHIFT_RIGHT, BinaryOperand.BIT_SHIFT_LEFT):
            return 6
        if self == BinaryOperand.CONCAT:
            return 7
        if self in (BinaryOperand.PLUS, BinaryOperand.MINUS):
            return 8
        if self in (
            BinaryOperand.MULT,
            BinaryOperand.DIVIDE,
            BinaryOperand.INTEGER_DIVISION,
            BinaryOperand.MODULO,
        ):
            return 9
        # precedence 10 is unop
        if self == BinaryOperand.EXPONENT:
            return 11
        assert False, f"Unknown Binary Operand {self}"


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
