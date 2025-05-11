from __future__ import annotations

import itertools
import string
from typing import TYPE_CHECKING, Iterator, Optional

from tumfl.AST import (
    Assign,
    ASTNode,
    Block,
    Expression,
    FunctionDefinition,
    MethodInvocation,
    Name,
    NamedIndex,
    Vararg,
)

if TYPE_CHECKING:
    from tumfl.minifier.shorten_names import ReplacementCollection, Replacements


def inner_add_alias(
    chunk: Block, current: Replacements, to_alias: list[Replacements], pos: list[int]
) -> None:
    if current.parent in to_alias:
        inner_add_alias(chunk, current.parent, to_alias, pos)
    if current in to_alias:
        to_alias.remove(current)
    assert current.replacement
    assert current.original
    token = current.original.token
    replacements: list[Replacements] = [current]
    while replacements[0].parent is not None:
        replacements.insert(0, replacements[0].parent)
    names: list[Name] = [replacement.targets[0] for replacement in replacements]
    parent_idx: int = -1
    if current.parent is not None:
        for i, name in enumerate(names):
            if name in current.parent.targets:
                parent_idx = i
                break
    names = [name if i <= parent_idx else name.clone() for i, name in enumerate(names)]
    node: Expression = names.pop(0)
    for name in names:
        node = NamedIndex(token, node, name)
    assign = Assign(
        token,
        [Name(token, current.replacement)],
        [node],
    )
    if current.after is None:
        chunk.statements.insert(pos[0], assign)
        pos[0] += 1
    else:
        previous_assign: Optional[ASTNode] = current.after.parent_class
        assert isinstance(previous_assign, Assign)
        parent_block = previous_assign.parent_class
        assert isinstance(parent_block, Block)
        idx: int = parent_block.statements.index(previous_assign)
        assert idx >= 0
        parent_block.statements.insert(idx + 1, assign)


def add_aliases(chunk: Block, to_alias: list[Replacements]) -> None:
    pos = [0]
    while to_alias:
        replacement = to_alias.pop(0)
        inner_add_alias(chunk, replacement, to_alias, pos)


def replace_name(name: Name, replacement: str) -> None:
    parent: Optional[ASTNode] = name.parent_class
    name.variable_name = replacement
    assert parent
    if isinstance(parent, FunctionDefinition):
        idx: int
        other_name: Name | Vararg
        for i, other_name in enumerate(parent.names):
            if other_name is name:
                idx = i
                break
        else:
            for other_name in parent.parameters:
                if other_name is name:
                    return
            raise NotImplementedError("Name can not be method")
        parent.names[: idx + 1] = [name]
    elif isinstance(parent, MethodInvocation):
        assert name is not parent.method
        raise NotImplementedError("TODO: Figure out")
    elif isinstance(parent, NamedIndex):
        if name is parent.variable_name:
            parent.replace(name)
        else:
            assert name is parent.lhs


def char_sequence() -> Iterator[str]:
    # Define the “alphabet” in order: a–z then A–Z
    alphabet = list(string.ascii_lowercase) + list(string.ascii_uppercase)
    length = 1
    while True:
        # For the current string-length `length`, yield all combinations in lexicographic order
        for tup in itertools.product(alphabet, repeat=length):
            yield "".join(tup)
        length += 1


def full_replace(chunk: Block, replacements: ReplacementCollection) -> None:
    for inner_loop, new_name in zip(replacements, char_sequence()):
        for replacement in inner_loop:
            replacement.replacement = new_name
    to_alias: list[Replacements] = []
    for inner_loop in replacements:
        for replacement in inner_loop:
            if replacement.original:
                to_alias.append(replacement)
    add_aliases(chunk, to_alias)
    for inner_loop in replacements:
        for replacement in inner_loop:
            assert replacement.replacement
            for name in replacement.targets:
                replace_name(name, replacement.replacement)
