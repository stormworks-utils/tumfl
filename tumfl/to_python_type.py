from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from tumfl.AST import (
    Assign,
    BinaryOperand,
    BinOp,
    Block,
    Boolean,
    Break,
    ExplicitTableField,
    Goto,
    Label,
    LocalAssign,
    Name,
    NamedTableField,
    Nil,
    Number,
    NumberedTableField,
    Semicolon,
    String,
    Table,
    UnaryOperand,
    UnOp,
    Vararg,
)
from tumfl.basic_walker import BasicWalker


class NilVal:
    """Pseudo class that defines an nil value, in order to differentiate it from None."""

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, NilVal)


if TYPE_CHECKING:
    Retype = Union[
        list["Retype"], dict["Retype", "Retype"], str, int, float, bool, None, NilVal
    ]
else:
    Retype = object


def to_bool(val: Retype) -> bool:
    return not isinstance(val, NilVal) and val is not False


class ToPythonType(BasicWalker[Retype]):
    # pylint: disable=duplicate-code
    def visit_Name(self, node: Name) -> Retype:
        pass

    def visit_Vararg(self, node: Vararg) -> Retype:
        pass

    def visit_Assign(self, node: Assign) -> Retype:
        pass

    def visit_Block(self, node: Block) -> Retype:
        pass

    def visit_Break(self, node: Break) -> Retype:
        pass

    def visit_Goto(self, node: Goto) -> Retype:
        pass

    def visit_Label(self, node: Label) -> Retype:
        pass

    def visit_LocalAssign(self, node: LocalAssign) -> Retype:
        pass

    def visit_Semicolon(self, node: Semicolon) -> Retype:
        pass

    def visit_Boolean(self, node: Boolean) -> Retype:
        return node.value

    def visit_Nil(self, node: Nil) -> Retype:
        return NilVal()

    def visit_Number(self, node: Number) -> Retype:
        int_repr: Optional[int] = node.to_int()
        return int_repr if int_repr is not None else node.to_float()

    def visit_String(self, node: String) -> Retype:
        return node.value

    def visit_Table(self, node: Table) -> Retype:
        results: dict[Retype, Retype] = {}
        index: int = 1
        for field in node.fields:
            field_value = self.visit(field.value)
            if field_value is None:
                return None
            if isinstance(field, NamedTableField):
                results[field.field_name.variable_name] = field_value
            elif isinstance(field, NumberedTableField):
                results[index] = field_value
                index += 1
            elif isinstance(field, ExplicitTableField):
                key_value = self.visit(field.at)
                if key_value is None:
                    return None
                results[key_value] = field_value
            else:
                raise NotImplementedError
        # pylint: disable=consider-iterating-dictionary
        if len(results) > 0 and all(isinstance(val, int) for val in results.keys()):
            max_key: int = max(results.keys())  # type: ignore
            min_key: int = min(results.keys())  # type: ignore
            if min_key == 1 and all(key in results for key in range(1, max_key + 1)):
                return [results[key] for key in range(1, max_key + 1)]
        return results

    def visit_UnOp(self, node: UnOp) -> Retype:
        rhs = self.visit(node.right)
        if rhs is None:
            return None
        if node.op == UnaryOperand.NOT:
            return not to_bool(rhs)
        if node.op == UnaryOperand.MINUS and isinstance(rhs, (int, float)):
            return -rhs
        if node.op == UnaryOperand.HASH and isinstance(rhs, (list, dict, str)):
            return len(rhs)
        if node.op == UnaryOperand.BIT_XOR and isinstance(rhs, (int, float)):
            return ~int(rhs)
        return None

    def visit_BinOp(self, node: BinOp) -> Retype:
        rhs = self.visit(node.right)
        lhs = self.visit(node.left)
        int_or_float = isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
        str_int_or_float = isinstance(lhs, (str, int, float)) and isinstance(
            rhs, (str, int, float)
        )
        bit_safe = (
            isinstance(lhs, (int, float))
            and isinstance(rhs, (int, float))
            and lhs % 1 == 0
            and rhs % 1 == 0
        )
        if rhs is None or lhs is None:
            return None
        if node.op == BinaryOperand.PLUS and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return lhs + rhs
        if node.op == BinaryOperand.MINUS and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return lhs - rhs
        if node.op == BinaryOperand.MULT and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return lhs * rhs
        if node.op == BinaryOperand.DIVIDE and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return float(lhs) / float(rhs)
        if node.op == BinaryOperand.MODULO and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return lhs % rhs
        if node.op == BinaryOperand.INTEGER_DIVISION and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs // rhs)
        if node.op == BinaryOperand.EXPONENT and int_or_float:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return float(lhs) ** float(rhs)
        if node.op == BinaryOperand.EQUALS and str_int_or_float:
            return lhs == rhs
        if node.op == BinaryOperand.NOT_EQUALS and str_int_or_float:
            return lhs != rhs
        if node.op == BinaryOperand.GREATER_THAN and str_int_or_float:
            if isinstance(lhs, str) and isinstance(rhs, str):
                return lhs > rhs
            if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
                return lhs > rhs
        if node.op == BinaryOperand.GREATER_EQUALS and str_int_or_float:
            if isinstance(lhs, str) and isinstance(rhs, str):
                return lhs >= rhs
            if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
                return lhs >= rhs
        if node.op == BinaryOperand.LESS_THAN and str_int_or_float:
            if isinstance(lhs, str) and isinstance(rhs, str):
                return lhs < rhs
            if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
                return lhs < rhs
        if node.op == BinaryOperand.LESS_EQUALS and str_int_or_float:
            if isinstance(lhs, str) and isinstance(rhs, str):
                return lhs <= rhs
            if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
                return lhs <= rhs
        if node.op == BinaryOperand.BIT_AND and bit_safe:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs) & int(rhs)
        if node.op == BinaryOperand.BIT_OR and bit_safe:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs) | int(rhs)
        if node.op == BinaryOperand.BIT_XOR and bit_safe:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs) ^ int(rhs)
        if node.op == BinaryOperand.BIT_SHIFT_LEFT and bit_safe:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs) << int(rhs)
        if node.op == BinaryOperand.BIT_SHIFT_RIGHT and bit_safe:
            assert isinstance(lhs, (int, float)) and isinstance(rhs, (int, float))
            return int(lhs) >> int(rhs)
        if node.op == BinaryOperand.CONCAT and str_int_or_float:
            assert isinstance(lhs, (str, int, float)) and isinstance(
                rhs, (str, int, float)
            )
            return str(lhs) + str(rhs)
        if node.op == BinaryOperand.AND:
            return lhs if not to_bool(lhs) else rhs
        if node.op == BinaryOperand.OR:
            return lhs if to_bool(lhs) else rhs
        return None
