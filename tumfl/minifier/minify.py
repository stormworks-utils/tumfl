from typing import Optional

from tumfl.AST import ASTNode, Chunk
from tumfl.minifier.block_optimization import Optimize
from tumfl.minifier.resolve_indexes import Resolve
from tumfl.minifier.shorten_names import GetNames, remove_unused_names
from tumfl.minifier.simplify_expressions import Simplify
from tumfl.minifier.util.replace_name import full_replace


def minify(ast: ASTNode, preserve_names: Optional[set[str]] = None) -> None:
    Resolve()(ast)
    r = GetNames()
    r(ast)
    remove_unused_names(ast, r, preserve_names or set())
    # print(r.current_scope)
    assert isinstance(ast, Chunk)
    replacements = r.current_scope.collect_replacements()
    full_replace(ast, replacements, preserve_names or set())
    Optimize()(ast)
    # CombineLocal()(ast) combine_local still contains flaws
    Simplify()(ast)
