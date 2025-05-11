from __future__ import annotations

from enum import Enum

from tumfl.Token import Token

from .expression import Expression


class UnaryOperand(Enum):
    MINUS = "-"
    HASH = "#"
    BIT_XOR = "~"
    NOT = "not"

    def __repr__(self) -> str:
        return f"UnaryOperand.{self.name}"


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
