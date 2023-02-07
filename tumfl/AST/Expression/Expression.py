from abc import ABC

from tumfl.AST.ASTNode import ASTNode


class Expression(ASTNode, ABC):
    """Base class for all expressions"""
