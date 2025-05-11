from __future__ import annotations

from typing import Optional

from tumfl.Token import Token, TokenType

from .expression import Expression


class Number(Expression):
    """A number, still preserved in the original representation, like 1.2, 3 or 0x123f"""

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

    def to_int(self) -> Optional[int]:
        if self.exponent or self.fractional_part or self.float_offset:
            # is a float
            return None
        assert self.integer_part
        return int(self.integer_part, 16) if self.is_hex else int(self.integer_part)

    def to_float(self) -> float:
        str_repr: str = str(self)
        if self.is_hex:
            return float.fromhex(str_repr)
        return float(str_repr)

    def __str__(self) -> str:
        str_repr: str = ""
        if self.is_hex:
            str_repr += "0x"
        if self.integer_part:
            str_repr += self.integer_part
        else:
            str_repr += "1" if self.is_hex else "0"
        if self.fractional_part:
            str_repr += f".{self.fractional_part}"
        if self.exponent:
            str_repr += f"e{self.exponent}"
        if self.float_offset:
            str_repr += f"p{self.float_offset}"
        return str_repr
