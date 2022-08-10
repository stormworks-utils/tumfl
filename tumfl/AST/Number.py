from __future__ import annotations

from typing import Optional, Any

from .ASTNode import ASTNode
from tumfl.Token import Token, TokenType


class Number(ASTNode):
    def __init__(
        self,
        token: Token,
        is_hex: bool = False,
        integer_part: Optional[str] = None,
        fractional_part: Optional[str] = None,
        exponent: Optional[str] = None,
        float_offset: Optional[str] = None,
    ):
        super().__init__(token, "Number")
        self.is_hex: bool = is_hex
        self.integer_part: Optional[str] = integer_part
        self.fractional_part: Optional[str] = fractional_part
        self.exponent: Optional[str] = exponent
        self.float_offset: Optional[str] = float_offset

    @staticmethod
    def from_token(token: Token) -> Number:
        assert token.type == TokenType.NUMBER
        value = token.value
        assert isinstance(value, tuple)
        return Number(
            token,
            is_hex=value[0],
            integer_part=value[1],
            fractional_part=value[2],
            exponent=value[3],
            float_offset=value[4],
        )

    def __repr__(self) -> str:
        return (
            f"Number("
            f"is_hex={self.is_hex!r}, "
            f"integer_part={self.integer_part!r}, "
            f"fractional_part={self.fractional_part!r}, "
            f"exponent={self.exponent!r}, "
            f"float_offset={self.float_offset!r})"
        )


"""    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Number):
            return (
                self.is_hex == other.is_hex
                and self.integer_part == other.integer_part
                and self.fractional_part == other.fractional_part
                and self.exponent == other.exponent
                and self.float_offset == other.float_offset
            )
        return False
"""
