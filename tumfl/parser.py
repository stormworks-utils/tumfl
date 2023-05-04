from __future__ import annotations
import sys
from typing import Optional, Callable, NoReturn

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
        self.context_hints: list[tuple[Token, str]] = []

    def error(self, message: str, token: Token) -> NoReturn:
        """Throw an error, prints out a description, and finally throws a value error"""
        current_line: int = token.line
        current_column = token.column
        print(f"Error on line {current_line}:", file=sys.stderr)
        print(self.lexer.text_by_line[current_line - 1], file=sys.stderr)
        print(" " * current_column + "^", file=sys.stderr)
        print(message, file=sys.stderr)
        if self.context_hints:
            print("hints:", ' -> '.join(f"{hint} ({token.line}:{token.column})" for token, hint in self.context_hints), file=sys.stderr)
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

    def _add_hint(self, verbal_hint: str) -> None:
        """Add a context hint for error messages"""
        self.context_hints.append((self.current_token, verbal_hint))

    def _remove_hint(self) -> None:
        """Remove a context hint for error messages"""
        self.context_hints.pop()

    def _switch_hint(self, verbal_hint: str) -> None:
        self._remove_hint()
        self._add_hint(verbal_hint)

    def parse_chunk(self) -> Chunk:
        """
        Parse a chunk

        chunk: block
        """
        block: Block = self._parse_block()
        return Chunk(block.token, block.statements, block.returns)

    def _parse_block(self) -> Block:
        """
        Parse a block

        block: (DO | REPEAT | THEN | ELSE) {stat} [RETURN explist [SEMICOLON]] [END]
        """
        block: Block = Block(self.current_token, [], [])
        self.eat_token()
        while self.current_token.type not in (
            TokenType.EOF,
            TokenType.END,
            TokenType.RETURN,
            TokenType.UNTIL
        ):
            block.statements.append(self._parse_statement())
        if self.current_token.type == TokenType.RETURN:
            self.eat_token(TokenType.RETURN)
            # TODO
        if self.current_token.type == TokenType.END:
            self.eat_token()
        return block

    def _parse_statement(self) -> Statement:
        """Parse a statement"""
        match self.current_token.type:
            case TokenType.BREAK:
                return self._parse_break()
            case TokenType.GOTO:
                return self._parse_goto()
            case TokenType.LABEL_BORDER:
                return self._parse_label()
            case TokenType.DO:
                return self._parse_block()
            case TokenType.WHILE:
                return self._parse_while()
            case TokenType.REPEAT:
                return self._parse_repeat()
            case TokenType.IF:
                return self._parse_if()

    def _parse_break(self) -> Break:
        """Parse a break statement"""
        return Break(self.current_token)

    def __eat_name(self) -> Name:
        """Eat a name token and return the string value"""
        name_token: Token = self.current_token
        self.eat_token(TokenType.NAME)
        return Name.from_token(name_token)

    def _parse_goto(self) -> Goto:
        """
        Parse a goto statement

        goto_stmt: GOTO Name
        """
        goto_token: Token = self.current_token
        self._add_hint("<goto> name")
        self.eat_token(TokenType.GOTO)
        name: Name = self.__eat_name()
        self._remove_hint()
        return Goto(goto_token, name)

    def _parse_label(self) -> Label:
        """
        Parse a label statement

        label_stmt: LABEL_BORDER Name LABEL_BORDER
        """
        opening_token: Token = self.current_token
        self._add_hint("<label> name")
        self.eat_token(TokenType.LABEL_BORDER)
        name: Name = self.__eat_name()
        self._switch_hint("<label> end")
        self.eat_token(TokenType.LABEL_BORDER)
        self._remove_hint()
        return Label(opening_token, name)

    def _parse_while(self) -> While:
        """
        Parse a while loop

        while_stmt: WHILE exp DO block END
        """
        while_token: Token = self.current_token
        self._add_hint("<while> condition")
        self.eat_token(TokenType.WHILE)
        condition: Expression = self._parse_exp()
        self._switch_hint("<while> block")
        self.eat_token(TokenType.DO)
        body: Block = self._parse_block()
        body.comment.extend(while_token.comment)
        self._remove_hint()
        return While(while_token, condition, body)

    def _parse_repeat(self) -> Repeat:
        """
        Parse a repeat until loop

        repeat_stmt: REPEAT block UNTIL exp END
        """
        repeat_token: Token = self.current_token
        self._add_hint("<repeat> block")
        self.eat_token(TokenType.REPEAT)
        body: Block = self._parse_block()
        body.comment.extend(repeat_token.comment)
        self._switch_hint("<repeat> condition")
        self.eat_token(TokenType.UNTIL)
        condition: Expression = self._parse_exp()
        self.eat_token(TokenType.END)
        self._remove_hint()
        return Repeat(repeat_token, condition, body)

    def _parse_if(self) -> If:
        """
        Parse an if statement

        if_stmt: IF exp THEN block {ELSEIF exp THEN block} [ELSE block] end
        """
        if_token: Token = self.current_token
        self._add_hint("<if> condition")
        self.eat_token(TokenType.IF)
        if_cond: Expression = self._parse_exp()
        self._switch_hint("<if> block")
        self.eat_token(TokenType.THEN)
        if_block: Block = self._parse_block()
        if_block.comment.extend(if_token.comment)
        elseif_tokens: list[Token] = []
        elseif_conditions: list[Expression] = []
        elseif_blocks: list[Block] = []
        while self.current_token.type == TokenType.ELSEIF:
            self._switch_hint("<elseif> condition")
            elseif_tokens.append(self.current_token)
            self.eat_token()
            elseif_conditions.append(self._parse_exp())
            self._switch_hint("<elseif> block")
            self.eat_token(TokenType.THEN)
            elseif_blocks.append(self._parse_block())
        else_block: Optional[Block] = None
        if self.current_token.type == TokenType.ELSE:
            self._switch_hint("<else> block")
            self.eat_token()
            else_block = self._parse_block()
        self._remove_hint()
        assert len(elseif_conditions) == len(elseif_blocks) and len(elseif_blocks) == len(elseif_tokens)
        current_if: Optional[If | Block] = else_block
        for i in range(len(elseif_conditions) - 1, -1, -1):
            elseif_blocks[i].comment.extend(if_token.comment)
            current_if = If(elseif_tokens[i], elseif_conditions[i], elseif_blocks[i], current_if)
        return If(if_token, if_cond, if_block, current_if)

    def _parse_for(self) -> IterativeFor | NumericFor:
        """
        Parses either an iterative or numeric for, depending on how it looks like

        for_stmt: num_for | it_for
        """
        for_token: Token = self.current_token
        self._add_hint("<for> name")
        self.eat_token(TokenType.FOR)
        first_name: Name = self.__eat_name()
        if self.current_token.type == TokenType.ASSIGN:
            return self._parse_numeric_for(for_token, first_name)
        elif self.current_token.type in (TokenType.COMMA, TokenType.IN):
            return self._parse_iterative_for(for_token, first_name)
        self.error("unexpected for condition", self.current_token)

    def _parse_numeric_for(self, for_token: Token, name: Name) -> NumericFor:
        """
        Parse a numeric for

        num_for: FOR Name ASSIGN exp COMMA exp [COMMA exp] DO block END
        """
        self._switch_hint("<numeric for> start expression")
        self.eat_token(TokenType.ASSIGN)
        start: Expression = self._parse_exp()
        self._switch_hint("<numeric for> stop expression")
        self.eat_token(TokenType.COMMA)
        stop: Expression = self._parse_exp()
        step: Optional[Expression] = None
        if self.current_token.type == TokenType.COMMA:
            self._switch_hint("<numeric for> step expression")
            self.eat_token()
            step = self._parse_exp()
        self._switch_hint("<numeric for> block")
        self.eat_token(TokenType.DO)
        body: Block = self._parse_block()
        body.comment.extend(for_token.comment)
        self._remove_hint()
        return NumericFor(for_token, name, start, stop, step, body)

    def _parse_iterative_for(self, for_token: Token, name: Name) -> IterativeFor:
        """
        Parse an iterative for

        it_for: FOR namelist IN explist DO block END
        """
        self._switch_hint("<iterative for> name list")
        names: list[Name] = self._parse_name_list(name)
        self._switch_hint("<iterative for> expression list")
        self.eat_token(TokenType.IN)
        expressions: list[Expression] = []
        while self.current_token.type == TokenType.COMMA:
            self.eat_token()
            expressions.append(self._parse_exp())
        self._switch_hint("<iterative for> block")
        self.eat_token(TokenType.DO)
        body: Block = self._parse_block()
        body.comment.extend(for_token.comment)
        self._remove_hint()
        return IterativeFor(for_token, names, expressions, body)

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
        self.error("Unexpected expression", self.current_token)

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

    def _parse_name_list(self, first_name: Optional[Name] = None) -> list[Name]:
        """
        Parse a list of names

        name_list: Name {COMMA Name}
        """
        names: list[Name] = [first_name] if first_name else []
        has_comma: bool = not first_name
        if first_name and self.current_token.type == TokenType.COMMA:
            self.eat_token()
            has_comma = True
        while self.current_token.type == TokenType.NAME and has_comma:
            names.append(Name.from_token(self.current_token))
            self.eat_token()
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
            else:
                has_comma = False
        return names
