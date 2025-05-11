from abc import ABC

from tumfl.AST.ast_node import ASTNode


class Expression(ASTNode, ABC):
    """Base class for all expressions"""
