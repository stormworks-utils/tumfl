from __future__ import annotations

from typing import NoReturn

from .AST import (
    ExpFunctionDefinition,
    FunctionDefinition,
    LocalFunctionDefinition,
    Name,
    Vararg,
)
from .basic_walker import NoneWalker
from .error import SemanticError
from .Token import Token


class SemanticAnalyzer(NoneWalker):
    def __init__(self) -> None:
        self.in_vararg_funct: bool = False

    def error(self, message: str, token: Token) -> NoReturn:
        raise SemanticError(message, token)

    @staticmethod
    def _param_contains_vararg(parameters: list[Name | Vararg]) -> bool:
        return any(isinstance(param, Vararg) for param in parameters)

    def visit_FunctionDefinition(self, node: FunctionDefinition) -> None:
        before: bool = self.in_vararg_funct
        self.in_vararg_funct = before or self._param_contains_vararg(node.parameters)
        super().visit_FunctionDefinition(node)
        self.in_vararg_funct = before

    def visit_ExpFunctionDefinition(self, node: ExpFunctionDefinition) -> None:
        before: bool = self.in_vararg_funct
        self.in_vararg_funct = before or self._param_contains_vararg(node.parameters)
        super().visit_ExpFunctionDefinition(node)
        self.in_vararg_funct = before

    def visit_LocalFunctionDefinition(self, node: LocalFunctionDefinition) -> None:
        before: bool = self.in_vararg_funct
        self.in_vararg_funct = before or self._param_contains_vararg(node.parameters)
        super().visit_LocalFunctionDefinition(node)
        self.in_vararg_funct = before

    def visit_Vararg(self, node: Vararg) -> None:
        if not self.in_vararg_funct:
            self.error("Vararg outside of vararg function", node.token)
