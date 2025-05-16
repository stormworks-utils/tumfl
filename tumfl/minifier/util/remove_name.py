from __future__ import annotations

from tumfl.AST import Name
from tumfl.basic_walker import NoneWalker
from tumfl.minifier.util.variable import Variable


class RemoveName(NoneWalker):
    def visit_Name(self, node: Name) -> None:
        if var := node.get_attribute(Variable):
            var.remove(node)
