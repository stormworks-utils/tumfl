from __future__ import annotations

from enum import Enum

from tumfl.Token import Token

from .Expression import Expression


class BinaryOperand(Enum):
    # pylint: disable=duplicate-code
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

    @property
    def __lvl2(self) -> tuple[BinaryOperand, ...]:
        return (
            BinaryOperand.EQUALS,
            BinaryOperand.NOT_EQUALS,
            BinaryOperand.LESS_EQUALS,
            BinaryOperand.GREATER_EQUALS,
            BinaryOperand.LESS_THAN,
            BinaryOperand.GREATER_THAN,
        )

    @property
    def __bitwise_operands(self) -> tuple[BinaryOperand, ...]:
        return (
            BinaryOperand.BIT_XOR,
            BinaryOperand.BIT_AND,
            BinaryOperand.BIT_SHIFT_LEFT,
            BinaryOperand.BIT_SHIFT_RIGHT,
            BinaryOperand.CONCAT,
            BinaryOperand.PLUS,
            BinaryOperand.MINUS,
        )

    @property
    def __lvl8(self) -> tuple[BinaryOperand, ...]:
        return (
            BinaryOperand.MULT,
            BinaryOperand.DIVIDE,
            BinaryOperand.INTEGER_DIVISION,
            BinaryOperand.MODULO,
        )

    def get_precedence(self) -> int:
        if self == BinaryOperand.OR:
            return 0
        if self == BinaryOperand.AND:
            return 1
        if self in self.__lvl2:
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
        if self in self.__lvl8:
            return 9
        # precedence 10 is unop
        if self == BinaryOperand.EXPONENT:
            return 11
        assert False, f"Unknown Binary Operand {self}"

    def get_optional_brackets(self) -> tuple[BinaryOperand, ...]:
        if self == BinaryOperand.OR:
            return (BinaryOperand.AND,)
        if self == BinaryOperand.AND:
            return ()
        if self in self.__lvl2:
            return self.__lvl2
        if self == BinaryOperand.BIT_OR:
            return self.__bitwise_operands
        if self == BinaryOperand.BIT_XOR:
            return self.__bitwise_operands
        if self == BinaryOperand.BIT_AND:
            return self.__bitwise_operands
        if self in (BinaryOperand.BIT_SHIFT_RIGHT, BinaryOperand.BIT_SHIFT_LEFT):
            return self.__bitwise_operands
        if self == BinaryOperand.CONCAT:
            return BinaryOperand.PLUS, BinaryOperand.MINUS
        if self in (BinaryOperand.PLUS, BinaryOperand.MINUS):
            return self.__lvl8
        if self in self.__lvl8:
            return (BinaryOperand.EXPONENT,)
        # precedence 10 is unop
        if self == BinaryOperand.EXPONENT:
            return ()
        assert False, f"Unknown Binary Operand {self}"

    def __repr__(self) -> str:
        return f"BinaryOperand.{self.name}"


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
