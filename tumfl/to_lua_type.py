import re

from tumfl.AST import (
    Boolean,
    ExplicitTableField,
    Expression,
    Name,
    NamedTableField,
    Nil,
    Number,
    NumberedTableField,
    String,
    Table,
    UnaryOperand,
    UnOp,
)
from tumfl.lexer import Lexer
from tumfl.to_python_type import NilVal, Retype
from tumfl.Token import Token, TokenType

NAME_REGEX: re.Pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def to_lua_type(python_type: Retype) -> Expression:
    if isinstance(python_type, dict):
        table = Table(Token(TokenType.L_CURL, "{", 0, 0), [])
        i = 1
        try:
            while True:
                val = python_type.pop(i)
                lua_value = to_lua_type(val)
                table.fields.append(NumberedTableField(lua_value.token, lua_value))
                i += 1
        except KeyError:
            pass
        for key, val in python_type.items():
            lua_value = to_lua_type(val)
            if isinstance(key, str) and NAME_REGEX.fullmatch(key):
                name = Name.from_token(Token(TokenType.NAME, key, 0, 0))
                table.fields.append(NamedTableField(name.token, name, lua_value))
            else:
                key_value = to_lua_type(key)
                table.fields.append(
                    ExplicitTableField(key_value.token, key_value, lua_value)
                )
        return table
    if isinstance(python_type, list):
        table = Table(Token(TokenType.L_CURL, "{", 0, 0), [])
        for field in python_type:
            lua_value = to_lua_type(field)
            table.fields.append(NumberedTableField(lua_value.token, lua_value))
        return table
    if isinstance(python_type, bool):
        return Boolean.from_token(
            Token(
                TokenType.TRUE if python_type else TokenType.FALSE, python_type, 0, 0
            ),
        )
    if isinstance(python_type, (int, float)):
        number = str(python_type)
        signed = number.startswith("-")
        if signed:
            number = number[1:]
        lexed_number = Lexer(number).get_number()
        ast_number: Expression = Number.from_token(
            Token(TokenType.NUMBER, lexed_number, 0, 0)
        )
        if signed:
            ast_number = UnOp(
                Token(TokenType.MINUS, "-", 0, 0), UnaryOperand.MINUS, ast_number
            )
        return ast_number
    if isinstance(python_type, str):
        return String.from_token(Token(TokenType.STRING, python_type, 0, 0))
    if isinstance(python_type, NilVal):
        return Nil.from_token(Token(TokenType.NIL, "nil", 0, 0))
    raise NotImplementedError(f'Can not convert "{python_type}" to lua type')
