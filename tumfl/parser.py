from __future__ import annotations
import sys
from typing import Optional, Callable

from .lexer import Lexer
from .AST import *
from .AST.BaseFunctionDefinition import BaseFunctionDefinition
from .Token import Token, TokenType


class Parser:
    def __init__(self, chunk: str):
        self.chunk: str = chunk
        self.lexer: Lexer = Lexer(self.chunk)
        self.tokens: list[Token] = []
        while (current_token := self.lexer.get_next_token()).type != TokenType.EOF:
            self.tokens.append(current_token)
        else:
            # adds the eof to the end of the token stream
            self.tokens.append(current_token)
        self.pos: int = 0
        self.current_token: Token = self.tokens[0]

    def error(self, message: str, token: Token) -> None:
        """Throw an error, prints out a description, and finally throws a value error"""
        current_line: int = token.line
        current_column = token.column
        print(f"Error on line {current_line + 1}:", file=sys.stderr)
        print(self.lexer.text_by_line[current_line], file=sys.stderr)
        print(" " * current_column + "^", file=sys.stderr)
        print(message, file=sys.stderr)
        raise ValueError(message)

    def get_token_at_pos(self, pos: int) -> Token:
        """Gets the token at the position, or EOF if the position is greater than the end"""
        return self.tokens[min(pos, len(self.tokens) - 1)]

    def eat_token(self, token_type: Optional[TokenType] = None) -> None:
        """Eats a specific token and throws an error, if the wrong token is found"""
        if not token_type or self.current_token.type == token_type:
            self.pos += 1
            self.current_token = self.get_token_at_pos(self.pos)
        else:
            self.error("Unexpected token", self.current_token)

    def peek(self, distance: int = 1) -> Token:
        """Peek for future tokens, returns EOF if the end is reached"""
        return self.get_token_at_pos(self.pos + distance)

    def parse_chunk(self) -> Chunk:
        """
        Parse a chunk

        chunk: block
        """
        block: Block = self._parse_block()
        return Chunk(block.token, block.comment, block.statements, block.returns)

    def _parse_block(self) -> Block:
        """
        Parse a block

        block: {stat} [RETURN explist [SEMICOLON]]
        """
        block: Block = Block(self.current_token, self.current_token.comment, [], [])
        while self.current_token.type not in (
            TokenType.EOF,
            TokenType.END,
            TokenType.RETURN,
        ):
            block.statements.append(self._parse_statement())
        if self.current_token.type == TokenType.RETURN:
            self.eat_token(TokenType.RETURN)
            # TODO
        return block

    def _parse_statement(self) -> Statement:
        """Parse a statement"""

    def __parse_left_associative_binop(
        self, types: tuple[TokenType, ...], base: Callable[[], Expression]
    ) -> Expression:
        """Parse a generic left associative binop"""
        node: Expression = base()
        while self.current_token.type in types:
            token: Token = self.current_token
            self.eat_token()
            node = BinOp.from_token(token, node, base())
        return node

    def __parse_right_associative_binop(
        self, type: TokenType, base: Callable[[], Expression]
    ) -> Expression:
        """Parse a generic right associative binop"""
        nodes: list[Expression] = [base()]
        tokens: list[Token] = []
        while self.current_token.type == type:
            tokens.append(self.current_token)
            self.eat_token()
            nodes.append(base())
        node: Expression = nodes[-1]
        for i in range(len(nodes) - 2, -1, -1):
            node = BinOp.from_token(tokens[i], nodes[i], node)
        return node

    def _parse_exp(self) -> Expression:
        """
        Parse an expression

        exp: and_exp {OR and_exp}
        """
        return self.__parse_left_associative_binop((TokenType.OR,), self._parse_and_exp)

    def _parse_and_exp(self) -> Expression:
        """
        Parse an and expression

        and_exp: comp_exp {OR comp_exp}
        """
        return self.__parse_left_associative_binop(
            (TokenType.AND,), self._parse_comp_exp
        )

    def _parse_comp_exp(self) -> Expression:
        """
        Parse a comparative expression

        comp_exp: bit_or_exp
                  {(LESS_THAN | GREATER_THAN | LESS_EQUALS | GREATER_EQUALS | NOT_EQUALS | EQUALS) bit_or_exp}
        """
        return self.__parse_left_associative_binop(
            (
                TokenType.LESS_THAN,
                TokenType.GREATER_THAN,
                TokenType.LESS_EQUALS,
                TokenType.GREATER_EQUALS,
                TokenType.NOT_EQUALS,
                TokenType.EQUALS,
            ),
            self._parse_bit_or_exp,
        )

    def _parse_bit_or_exp(self) -> Expression:
        """
        Parse a bitwise or expression

        bit_or_exp: bit_xor_exp {BIT_OR bit_xor_exp}
        """
        return self.__parse_left_associative_binop(
            (TokenType.BIT_OR,), self._parse_bit_xor_exp
        )

    def _parse_bit_xor_exp(self) -> Expression:
        """
        Parse a bitwise and expression

        bit_xor_exp: bit_and_expr {BIT_XOR bit_and_expr}
        """
        return self.__parse_left_associative_binop(
            (TokenType.BIT_XOR,), self._parse_bit_and_exp
        )

    def _parse_bit_and_exp(self) -> Expression:
        """
        Parse a bitwise and expression

        bit_and_exp: bit_shift_exp {BIT_AND bit_shift_exp}
        """
        return self.__parse_left_associative_binop(
            (TokenType.BIT_AND,), self._parse_bit_shift_exp
        )

    def _parse_bit_shift_exp(self) -> Expression:
        """
        Parse a bit shift expression

        bit_shift_exp: concat_exp {(BIT_SHIFT_LEFT | BIT_SHIFT_RIGHT) concat_exp}
        """
        return self.__parse_left_associative_binop(
            (TokenType.BIT_SHIFT_LEFT, TokenType.BIT_SHIFT_RIGHT),
            self._parse_concat_exp,
        )

    def _parse_concat_exp(self) -> Expression:
        """
        Parse a concat expression, right associative

        concat_exp: add_exp {CONCAT add_exp}
        """
        return self.__parse_right_associative_binop(
            TokenType.CONCAT, self._parse_add_exp
        )

    def _parse_add_exp(self) -> Expression:
        """
        Parse a addition or subtraction expression

        add_exp: mul_exp {(PLUS | MINUS) mul_exp}
        """
        return self.__parse_left_associative_binop(
            (TokenType.PLUS, TokenType.MINUS), self._parse_mul_exp
        )

    def _parse_mul_exp(self) -> Expression:
        """
        Parse a multiplication or division expression

        mul_exp: un_exp {(MULT | DIVIDE | INTEGER_DIVISION | MODULO) un_exp}
        """
        return self.__parse_left_associative_binop(
            (
                TokenType.MULT,
                TokenType.DIVIDE,
                TokenType.INTEGER_DIVISION,
                TokenType.MODULO,
            ),
            self._parse_un_exp,
        )

    def _parse_un_exp(self) -> Expression:
        """
        Parse an unary expression

        un_exp: pow_exp | NOT un_exp | HASH un_exp | MINUS un_exp | BIT_XOR un_exp
        """
        if self.current_token.type in (
            TokenType.NOT,
            TokenType.HASH,
            TokenType.MINUS,
            TokenType.BIT_XOR,
        ):
            token = self.current_token
            self.eat_token()
            return UnOp.from_token(token, self._parse_un_exp())
        return self._parse_pow_exp()

    def _parse_pow_exp(self) -> Expression:
        """
        Parse a exponentiation expression, right associative

        pow_exp: atom {EXPONENT atom}
        """
        return self.__parse_right_associative_binop(
            TokenType.EXPONENT, self._parse_atom
        )

    def _parse_atom(self) -> Expression:
        """
        Parse an atom

        atom: NIL | TRUE | FALSE | NUMBER | STRING | ELLIPSIS | FUNCTION func_def | TODO
        """
        token: Token = self.current_token
        if token.type == TokenType.NIL:
            self.eat_token()
            return Nil.from_token(token)
        elif token.type == TokenType.TRUE:
            self.eat_token()
            return Boolean.from_token(token)
        elif token.type == TokenType.FALSE:
            self.eat_token()
            return Boolean.from_token(token)
        elif token.type == TokenType.NUMBER:
            self.eat_token()
            return Number.from_token(token)
        elif token.type == TokenType.STRING:
            self.eat_token()
            return String.from_token(token)
        elif token.type == TokenType.ELLIPSIS:
            self.eat_token()
            return Vararg.from_token(token)
        elif token.type == TokenType.FUNCTION:
            self.eat_token()
            base_function: BaseFunctionDefinition = self._parse_function_definition()
            return ExpFunctionDefinition.from_base_definition(base_function)
        raise NotImplementedError

    def _parse_function_definition(self) -> BaseFunctionDefinition:
        """
        Parse a bare function definition

        func_def: L_PAREN (name_list [COMMA ELLIPSIS] | ELLIPSIS) R_PAREN block END
        """
        token: Token = self.current_token
        parameters: list[Name | Vararg] = []
        self.eat_token(TokenType.L_PAREN)
        if self.current_token.type == TokenType.NAME:
            parameters.extend(self._parse_name_list())
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
                if self.current_token.type == TokenType.ELLIPSIS:
                    parameters.append(Vararg.from_token(self.current_token))
                    self.eat_token()
        elif self.current_token.type == TokenType.ELLIPSIS:
            parameters.append(Vararg.from_token(self.current_token))
            self.eat_token()
        self.eat_token(TokenType.R_PAREN)
        block: Block = self._parse_block()
        self.eat_token(TokenType.END)
        return BaseFunctionDefinition(token, parameters, block)

    def _parse_name_list(self) -> list[Name]:
        """
        Parse a list of names

        name_list: Name {COMMA Name}
        """
        names: list[Name] = []
        has_comma: bool = True
        while self.current_token.type == TokenType.NAME and has_comma:
            names.append(Name.from_token(self.current_token))
            self.eat_token()
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
            else:
                has_comma = False
        return names
