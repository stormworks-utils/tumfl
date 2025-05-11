import re

from tumfl.basic_walker import (
    ExplicitTableField,
    Index,
    Name,
    NamedIndex,
    NamedTableField,
    NoneWalker,
    String,
)
from tumfl.lexer import RESERVED_KEYWORDS

VALID_NAME: re.Pattern[str] = re.compile(r"[a-zA-Z_][a-zA-Z_0-9]*")


def is_valid_name(name: str) -> bool:
    return bool(VALID_NAME.fullmatch(name)) and name not in RESERVED_KEYWORDS


class Resolve(NoneWalker):
    """
    replaces `foo["bar"]` with `foo.bar` and {"foo"=...} with {foo=...}
    This is mostly done in order to simplify further minifications
    """

    def visit_ExplicitTableField(self, node: ExplicitTableField) -> None:
        if isinstance(node.at, String) and is_valid_name(node.at.name):
            new_node = NamedTableField(
                node.token, Name(node.at.token, node.at.value), node.value
            )
            node.replace(new_node)
        else:
            super().visit_ExplicitTableField(node)

    def visit_Index(self, node: Index) -> None:
        if isinstance(node.variable_name, String) and is_valid_name(
            node.variable_name.value
        ):
            new_node = NamedIndex(
                node.token,
                node.lhs,
                Name(node.variable_name.token, node.variable_name.value),
            )
            node.replace(new_node)
        else:
            super().visit_Index(node)
