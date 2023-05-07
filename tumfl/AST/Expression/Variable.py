from __future__ import annotations

from abc import ABC

from .Expression import Expression


class Variable(Expression, ABC):
    """Base class for all variable types"""
