from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .Boolean import Boolean
    from .Number import Number
    from .String import String
    from .Variable import Variable

PrefixExpression = Union[Variable]

Expression = Union[Boolean, Number, String, PrefixExpression]
