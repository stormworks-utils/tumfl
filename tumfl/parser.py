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
        self.context_hints: list[tuple[Token, str, str]] = []

    def error(self, message: str, token: Token) -> NoReturn:
        """Throw an error, prints out a description, and finally throws a value error"""
        current_line: int = token.line
        current_column = token.column
        print(f"Error on line {current_line}:", file=sys.stderr)
        print(self.lexer.text_by_line[current_line - 1], file=sys.stderr)
        print(" " * current_column + "^", file=sys.stderr)
        print(message, file=sys.stderr)
        if self.context_hints:
            print("hints:", ' -> '.join(f"<{where}> {what} ({token.line}:{token.column})" for token, where, what in self.context_hints), file=sys.stderr)
        raise ValueError(message)

    def get_token_at_pos(self, pos: int) -> Token:
        """Gets the token at the position, or EOF if the position is greater than the end"""
        return self.tokens[min(pos, len(self.tokens) - 1)]

    def _assert(self, token_type: TokenType) -> None:
        """Assert that the current token is of a certain kind"""
        if self.current_token.type != token_type:
            self.error("Unexpected token", self.current_token)

    def eat_token(self, token_type: Optional[TokenType] = None) -> None:
        """Eats a specific token and throws an error, if the wrong token is found"""
        if token_type:
            self._assert(token_type)
        self.pos += 1
        self.current_token = self.get_token_at_pos(self.pos)

    def peek(self, distance: int = 1) -> Token:
        """Peek for future tokens, returns EOF if the end is reached"""
        return self.get_token_at_pos(self.pos + distance)

    def _add_hint(self, where: str, what: str) -> None:
        """Add a context hint for error messages"""
        self.context_hints.append((self.current_token, where, what))

    def _remove_hint(self) -> tuple[Token, str, str]:
        """Remove a context hint for error messages"""
        return self.context_hints.pop()

    def _switch_hint(self, what: str) -> None:
        _, where, _ = self._remove_hint()
        self._add_hint(where, what)

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
            block.returns = self._parse_exp_list()
        if self.current_token.type == TokenType.END:
            self.eat_token()
        return block

    def _parse_statement(self) -> Statement:
        """Parse a statement"""
        match self.current_token.type:
            case TokenType.SEMICOLON:
                return self._parse_semi()
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
            case TokenType.FOR:
                return self._parse_for()
            case TokenType.FUNCTION:
                return self._parse_function()
            case TokenType.LOCAL:
                return self._parse_local()
        self.error("Unexpected statement", self.current_token)

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
        self._add_hint("goto", "name")
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
        self._add_hint("label", "name")
        self.eat_token(TokenType.LABEL_BORDER)
        name: Name = self.__eat_name()
        self._switch_hint("end")
        self.eat_token(TokenType.LABEL_BORDER)
        self._remove_hint()
        return Label(opening_token, name)

    def _parse_while(self) -> While:
        """
        Parse a while loop

        while_stmt: WHILE exp DO block END
        """
        while_token: Token = self.current_token
        self._add_hint("while", "condition")
        self.eat_token(TokenType.WHILE)
        condition: Expression = self._parse_exp()
        self._switch_hint("block")
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
        self._add_hint("repeat", "block")
        self.eat_token(TokenType.REPEAT)
        body: Block = self._parse_block()
        body.comment.extend(repeat_token.comment)
        self._switch_hint("condition")
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
        self._add_hint("if", "if condition")
        self.eat_token(TokenType.IF)
        if_cond: Expression = self._parse_exp()
        self._switch_hint("if block")
        self.eat_token(TokenType.THEN)
        if_block: Block = self._parse_block()
        if_block.comment.extend(if_token.comment)
        elseif_tokens: list[Token] = []
        elseif_conditions: list[Expression] = []
        elseif_blocks: list[Block] = []
        while self.current_token.type == TokenType.ELSEIF:
            self._switch_hint("elseif condition")
            elseif_tokens.append(self.current_token)
            self.eat_token()
            elseif_conditions.append(self._parse_exp())
            self._switch_hint("elseif block")
            self.eat_token(TokenType.THEN)
            elseif_blocks.append(self._parse_block())
        else_block: Optional[Block] = None
        if self.current_token.type == TokenType.ELSE:
            self._switch_hint("else block")
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
        self._add_hint("for", "name")
        self.eat_token(TokenType.FOR)
        first_name: Name = self.__eat_name()
        self._remove_hint()
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
        self._add_hint("numeric for", "start expression")
        self.eat_token(TokenType.ASSIGN)
        start: Expression = self._parse_exp()
        self._switch_hint("stop expression")
        self.eat_token(TokenType.COMMA)
        stop: Expression = self._parse_exp()
        step: Optional[Expression] = None
        if self.current_token.type == TokenType.COMMA:
            self._switch_hint("step expression")
            self.eat_token()
            step = self._parse_exp()
        self._switch_hint("block")
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
        self._add_hint("iterative for", "name list")
        names: list[Name] = self._parse_name_list(name)
        self._switch_hint("expression list")
        self.eat_token(TokenType.IN)
        expressions: list[Expression] = self._parse_exp_list()
        self._switch_hint("block")
        self.eat_token(TokenType.DO)
        body: Block = self._parse_block()
        body.comment.extend(for_token.comment)
        self._remove_hint()
        return IterativeFor(for_token, names, expressions, body)

    def _parse_function(self) -> FunctionDefinition:
        """
        Parse a non-local function statement

        funct_stmt: FUNCTION Name {DOT Name} [COLON Name] funcbody
        """
        function_token: Token = self.current_token
        self._add_hint("function", "name")
        self.eat_token(TokenType.FUNCTION)
        names: list[Name] = [self.__eat_name()]
        while self.current_token.type == TokenType.COMMA:
            self.eat_token()
            names.append(self.__eat_name())
        method: Optional[Name] = None
        if self.current_token.type == TokenType.COLON:
            self._switch_hint("method name")
            self.eat_token()
            method = self.__eat_name()
        base_function: BaseFunctionDefinition = self._parse_funcbody(function_token)
        return FunctionDefinition.from_base_definition(base_function, names, method)

    def _parse_funcbody(self, function_token: Token) -> BaseFunctionDefinition:
        """
        Parse a function body (starting from parameters till end)

        funcbody: L_PAREN [namelist [COMMA ELLIPSIS] | ELLIPSIS] R_PAREN block END
        """
        self._switch_hint("parameters")
        self.eat_token(TokenType.L_PAREN)
        parameters: list[Name | Vararg] = []
        if self.current_token.type == TokenType.NAME:
            parameters.extend(self._parse_name_list())
            if self.current_token.type == TokenType.ELLIPSIS:
                self._switch_hint("varargs")
                parameters.append(Vararg.from_token(self.current_token))
                self.eat_token()
        elif self.current_token.type == TokenType.ELLIPSIS:
            self._switch_hint("varargs")
            parameters.append(Vararg.from_token(self.current_token))
            self.eat_token()
        self._switch_hint("body")
        body: Block = self._parse_block()
        body.comment.extend(function_token.comment)
        self._remove_hint()
        return BaseFunctionDefinition(function_token, parameters, body)

    def _parse_local(self) -> LocalFunctionDefinition | LocalAssign:
        """
        Parse a local function definition or local assign

        local_stmt: local_funct_stmt | local_assign_stmt
        """
        local_token: Token = self.current_token
        self.eat_token(TokenType.LOCAL)
        if self.current_token.type == TokenType.FUNCTION:
            return self._parse_local_function(local_token)
        elif self.current_token.type == TokenType.NAME:
            return self._parse_local_assignment(local_token)
        self.error("Unexpected symbol after local", self.current_token)

    def _parse_local_function(self, local_token: Token) -> LocalFunctionDefinition:
        """
        Parse a local function definition

        local_funct_stmt: LOCAL FUNCTION Name funcbody
        """
        self._add_hint("local function", "name")
        function_token: Token = self.current_token
        function_token.comment.extend(local_token.comment)
        self.eat_token(TokenType.FUNCTION)
        name: Name = self.__eat_name()
        base_function: BaseFunctionDefinition = self._parse_funcbody(function_token)
        return LocalFunctionDefinition.from_base_definition(base_function, name)

    def _parse_local_assignment(self, local_token: Token) -> LocalAssign:
        """
        Parse a local assign

        local_assign_stmt: LOCAL Name [LESS_THAN Name GREATER_THAN] {COMMA Name [LESS_THAN Name GREATER_THAN]} [ASSIGN explist]
        """
        self._add_hint("local assign", "names")
        self._assert(TokenType.NAME)
        names: list[AttributedName] = []
        while True:
            self._switch_hint("name")
            name: Name = self.__eat_name()
            attribute: Optional[Name] = None
            if self.current_token.type == TokenType.LESS_THAN:
                self._switch_hint("name attribute")
                self.eat_token()
                attribute = self.__eat_name()
                self.eat_token(TokenType.GREATER_THAN)
            names.append(AttributedName(name, attribute))
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
            else:
                break
        expressions: Optional[list[Expression]] = None
        if self.current_token.type == TokenType.ASSIGN:
            self._switch_hint("expressions")
            self.eat_token()
            expressions = self._parse_exp_list()
        return LocalAssign(local_token, names, expressions)

    def _parse_exp_list(self) -> list[Expression]:
        """
        Parse a list of expressions

        explist: exp {COMMA exp}
        """
        expressions: list[Expression] = []
        while True:
            expressions.append(self._parse_exp())
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
            else:
                break
        return expressions

    def _parse_semi(self) -> Semicolon:
        """
        Parse a semicolon

        semi_stmt: SEMICOLON
        """
        semicolon_token: Token = self.current_token
        self.eat_token(TokenType.SEMICOLON)
        return Semicolon(semicolon_token)

    def _parse_var_stmt(self) -> FunctionCall | MethodInvocation | Assign:
        """
        Parse a variable assignment or a function

        var_funct: assign_stmt | funct_call_stmt
        """
        first_token: Token = self.current_token
        first_var: Expression = self._parse_var()
        if self.current_token.type in (TokenType.COMMA, TokenType.ASSIGN):
            return self._parse_assignment(first_token, first_var)
        elif isinstance(first_var, ExpFunctionCall):
            return FunctionCall(first_var.token, first_var.function, first_var.arguments)
        elif isinstance(first_var, ExpMethodInvocation):
            return MethodInvocation(first_var.token, first_var.function, first_var.method, first_var.arguments)
        self.error("unexpected token after variable", self.current_token)

    def _parse_assignment(self, first_token: Token, first_var: Expression) -> Assign:
        """
        Parse an assignment

        assign_stmt: var {COMMA var} ASSIGN explist
        """
        variables: list[Expression] = [first_var]
        self._add_hint("assignment", "variables")
        while self.current_token.type == TokenType.COMMA:
            self.eat_token()
            variables.append(self._parse_var())
        self._switch_hint("expressions")
        expressions: list[Expression] = self._parse_exp_list()
        self._remove_hint()
        return Assign(first_token, variables, expressions)

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

        atom: NIL | TRUE | FALSE | NUMBER | STRING | ELLIPSIS | FUNCTION func_def | tableconstructor | var
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
            function_token: Token = self.current_token
            self._add_hint("function expression", "definition")
            self.eat_token()
            base_function: BaseFunctionDefinition = self._parse_funcbody(function_token)
            return ExpFunctionDefinition.from_base_definition(base_function)
        elif token.type == TokenType.R_CURL:
            return self._parse_table_constructor()
        elif token.type in (TokenType.L_PAREN, TokenType.NAME):
            return self._parse_var()
        self.error("Unexpected expression", self.current_token)

    def _parse_name_list(self, first_name: Optional[Name] = None) -> list[Name]:
        """
        Parse a list of names

        name_list: Name {COMMA Name}
        """
        names: list[Name] = [first_name] if first_name else []
        if first_name and self.current_token.type == TokenType.COMMA:
            self.eat_token()
        while self.current_token.type == TokenType.NAME:
            names.append(self.__eat_name())
            if self.current_token.type == TokenType.COMMA:
                self.eat_token()
            else:
                break
        return names

    def _parse_var(self) -> Expression:
        """
        Parse a variable. Might be either a Variable, function call, method invocation, index, named index,
        or any other expression

        var: Name | L_PAREN exp R_PAREN
        """
        var: Expression
        if self.current_token.type == TokenType.NAME:
            self._add_hint("named var", "name")
            var = self.__eat_name()
        elif self.current_token.type == TokenType.L_PAREN:
            self._add_hint("expression var", "expression")
            self.eat_token()
            var = self._parse_exp()
            self.eat_token(TokenType.R_PAREN)
        else:
            self.error("Unexpected variable", self.current_token)
            assert False
        var = self._parse_or_ignore_var_terminal(var)
        self._remove_hint()
        return var

    def _parse_or_ignore_var_terminal(self, base_var: Expression) -> Expression:
        """
        Parse a var terminal if necessary
        """
        if self.current_token.type in (TokenType.L_BRACKET, TokenType.DOT, TokenType.L_PAREN, TokenType.L_CURL, TokenType.COLON, TokenType.STRING):
            base_var = self._parse_var_terminal(base_var)
        return base_var

    def _parse_var_terminal(self, base_var: Expression) -> Expression:
        """
        Parse a variable terminal,

        var_terminal: var | var_terminal L_BRACKET exp R_BRACKET | var_terminal DOT Name | var_terminal args |
            var_terminal COLON Name args
        """
        token: Token = self.current_token
        var: Expression
        name: Name
        match token.type:
            case TokenType.L_PAREN | TokenType.L_CURL | TokenType.STRING:
                return ExpFunctionCall(token, base_var, self._parse_args())
            case TokenType.COLON:
                self._add_hint("invocation", "name")
                self.eat_token()
                name = self.__eat_name()
                self._remove_hint()
                args: list[Expression] = self._parse_args()
                return ExpMethodInvocation(token, base_var, name, args)
            case TokenType.L_BRACKET:
                self._add_hint("index", "expression")
                self.eat_token()
                expr: Expression = self._parse_exp()
                self.eat_token(TokenType.R_BRACKET)
                var = Index(token, base_var, expr)
            case TokenType.DOT:
                self._add_hint("index", "name")
                self.eat_token()
                name = self.__eat_name()
                var = NamedIndex(token, base_var, name)
            case _:
                self.error("Unknown var terminal", self.current_token)
                assert False
        var = self._parse_or_ignore_var_terminal(var)
        return var

    def _parse_table_constructor(self) -> Table:
        """
        Parse a table constructor

        tableconstructor: L_CURL [field {(COMMA | SEMICOLON) field} (COMMA | SEMICOLON)] R_CURL
        """
        table: Table = Table(self.current_token, [])
        self._add_hint("table constructor", "fields")
        self.eat_token(TokenType.L_CURL)
        while self.current_token.type not in (TokenType.R_CURL, TokenType.EOF):
            table.fields.append(self._parse_field())
            if self.current_token.type in (TokenType.COMMA, TokenType.SEMICOLON):
                self.eat_token()
        self.eat_token(TokenType.R_CURL)
        self._remove_hint()
        return table

    def _parse_field(self) -> TableField:
        """
        Parse a table field

        field: L_BRACKET exp R_BRACKET ASSIGN exp | Name ASSIGN exp | exp
        """
        token: Token = self.current_token
        value: Expression
        if self.current_token.type == TokenType.L_BRACKET:
            self._add_hint("explicit table field", "key expression")
            self.eat_token()
            at: Expression = self._parse_exp()
            self.eat_token(TokenType.R_BRACKET)
            self._switch_hint("value expression")
            self.eat_token(TokenType.ASSIGN)
            value = self._parse_exp()
            self._remove_hint()
            return ExplicitTableField(token, at, value)
        elif self.current_token.type == TokenType.NAME:
            self._add_hint("named table field", "name")
            name: Name = self.__eat_name()
            self._switch_hint("value expression")
            self.eat_token(TokenType.ASSIGN)
            value = self._parse_exp()
            self._remove_hint()
            return NamedTableField(token, name, value)
        self._add_hint("numbered table field", "expression")
        value = self._parse_exp()
        self._remove_hint()
        return NumberedTableField(token, value)

    def _parse_args(self) -> list[Expression]:
        """
        Parse an argument array for a function call

        args: L_PAREN [explist] R_PAREN | tableconstructor | LiteralString
        """
        self._add_hint("function call", "arguments")
        expressions: list[Expression] = []
        if self.current_token.type == TokenType.L_PAREN:
            self.eat_token()
            expressions = self._parse_exp_list()
            self.eat_token(TokenType.R_PAREN)
        elif self.current_token.type == TokenType.L_CURL:
            expressions.append(self._parse_table_constructor())
        elif self.current_token.type == TokenType.STRING:
            expressions.append(String.from_token(self.current_token))
        else:
            self.error("Unexpected function arguments", self.current_token)
        self._remove_hint()
        return expressions
