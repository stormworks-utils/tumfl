from __future__ import annotations

from enum import Enum

from tumfl.Token import Token, TokenType

from .Expression import Expression


class UnaryOperand(Enum):
    MINUS = "-"
    HASH = "#"
    BIT_XOR = "~"
    NOT = "not"


class UnOp(Expression):
    """A unary operation, like -a, #c or not true"""

    def __init__(self, token: Token, op: UnaryOperand, right: Expression) -> None:
        super().__init__(token, "UnOp")
        self.op: UnaryOperand = op
        self.right: Expression = right

    @staticmethod
    def from_token(token: Token, right: Expression) -> UnOp:
        unop: UnaryOperand = UnaryOperand[token.type.name]
        assert unop
        return UnOp(token, unop, right)
