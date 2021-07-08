import copy
from typing import Callable, Optional, TypeVar

import d20  # this import is here for the doctests
from d20 import diceast, expression
from .dice import AdvType

TreeType = TypeVar('TreeType', bound=diceast.ChildMixin)
ASTNode = TypeVar('ASTNode', bound=diceast.Node)
ExpressionNode = TypeVar('ExpressionNode', bound=expression.Number)


def ast_adv_copy(ast: ASTNode, advtype: AdvType) -> ASTNode:
    """
    Returns a minimally shallow copy of a dice AST with respect to advantage.

    >>> tree = d20.parse("1d20 + 5")
    >>> str(tree)
    '1d20 + 5'
    >>> str(ast_adv_copy(tree, d20.AdvType.ADV))
    '2d20kh1 + 5'

    :param d20.ast.Node ast: The parsed AST.
    :param AdvType advtype: The advantage type to roll at.
    :returns: The copied AST.
    :rtype: d20.ast.Node
    """
    root = copy.copy(ast)
    if not advtype:
        return root

    # find the leftmost node, making shallow copies all the way down
    parent = child = root
    while child.children:
        parent = child
        parent.left = child = copy.copy(parent.left)

    # is it dice?
    if not isinstance(child, diceast.Dice):
        return root

    # is it 1d20?
    if not (child.num == 1 and child.size == 20):
        return root

    # does it already have operations?
    if not isinstance(parent, diceast.OperatedDice):
        new_parent = diceast.OperatedDice(child)
        parent.left = new_parent
        parent = new_parent
    else:
        parent.operations = parent.operations.copy()

    # make the child 2d20
    child.num = 2

    # add the kh1 operator
    if advtype == 1:
        high_or_low = diceast.SetSelector('h', 1)
    else:
        high_or_low = diceast.SetSelector('l', 1)
    kh1 = diceast.SetOperator('k', [high_or_low])
    parent.operations.insert(0, kh1)

    return root


def simplify_expr_annotations(expr: ExpressionNode, ambig_inherit: Optional[str] = None):
    """
    Transforms an expression in place by simplifying the annotations using a bubble-up method.

    >>> roll_expr = d20.roll("1d20[foo]+3").expr
    >>> simplify_expr_annotations(roll_expr.roll)
    >>> d20.SimpleStringifier().stringify(roll_expr)
    "1d20 (4) + 3 [foo] = 7"

    :param d20.Number expr: The expression to transform.
    :param ambig_inherit: When encountering a child node with no annotation and the parent has ambiguous types, which
        to inherit. Can be ``None`` for no inherit, ``'left'`` for leftmost, or ``'right'`` for rightmost.
    :type ambig_inherit: Optional[str]
    """
    if ambig_inherit not in ('left', 'right', None):
        raise ValueError("ambig_inherit must be 'left', 'right', or None.")

    def do_simplify(node):
        possible_types = []
        child_possibilities = {}
        for child in node.children:
            child_possibilities[child] = do_simplify(child)
            possible_types.extend(t for t in child_possibilities[child] if t not in possible_types)
        if node.annotation is not None:
            possible_types.append(node.annotation)

        # if I have no type or the same as children and all my children have the same type, inherit
        if len(possible_types) == 1:
            node.annotation = possible_types[0]
            for child in node.children:
                child.annotation = None
        # if there are ambiguous types, resolve children by ambiguity rules
        # unless it would change the right side of a multiplicative binop
        elif len(possible_types) and ambig_inherit is not None:
            for i, child in enumerate(node.children):
                if child_possibilities[child]:  # if the child already provides an annotation or ambiguity
                    continue
                elif isinstance(node, expression.BinOp) \
                        and node.op in {'*', '/', '//', '%'} \
                        and i:  # if the child is the right side of a multiplicative binop
                    continue
                elif ambig_inherit == 'left':
                    child.annotation = possible_types[0]
                elif ambig_inherit == 'right':
                    child.annotation = possible_types[-1]

        # return all possible types
        return tuple(possible_types)

    do_simplify(expr)


def simplify_expr(expr: expression.Expression, **kwargs):
    """
    Transforms an expression in place by simplifying it (removing all dice and evaluating branches with respect to
    annotations).

    >>> roll_expr = d20.roll("1d20[foo] + 3 - 1d4[bar]").expr
    >>> simplify_expr(roll_expr)
    >>> d20.SimpleStringifier().stringify(roll_expr)
    "7 [foo] - 2 [bar] = 5"

    :param d20.Expression expr: The expression to transform.
    :param kwargs: Arguments that are passed to :func:`simplify_expr_annotations`.
    """
    simplify_expr_annotations(expr.roll, **kwargs)

    def do_simplify(node, first=False):
        """returns a pair of (replacement, branch had replacement)"""
        if node.annotation:
            return expression.Literal(node.total, annotation=node.annotation), True

        # pass 1: recursively replace branches with annotations, marking which branches had replacements
        had_replacement = set()
        for i, child in enumerate(node.children):
            replacement, branch_had = do_simplify(child)
            if branch_had:
                had_replacement.add(i)
            if replacement is not child:
                node.set_child(i, replacement)

        # pass 2: replace no-annotation branches
        for i, child in enumerate(node.children):
            if (i not in had_replacement) and (had_replacement or first):
                # here is the furthest we can bubble up a no-annotation branch
                replacement = expression.Literal(child.total)
                node.set_child(i, replacement)

        return node, bool(had_replacement)

    do_simplify(expr, True)


def tree_map(func: Callable[[TreeType], TreeType], node: TreeType) -> TreeType:
    """
    Returns a copy of the tree, with each node replaced with ``func(node)``.

    :param func: A transformer function.
    :type func: Callable[[d20.ast.ChildMixin], d20.ast.ChildMixin]
    :param node: The root of the tree to transform.
    :type node: d20.ast.ChildMixin
    :rtype: d20.ast.ChildMixin
    """
    copied = copy.copy(node)
    for i, child in enumerate(copied.children):
        copied.set_child(i, tree_map(func, child))
    return func(copied)


def leftmost(root: TreeType) -> TreeType:
    """
    Returns the leftmost leaf in this tree.

    :param d20.ast.ChildMixin root: The root node of the tree.
    :rtype: d20.ast.ChildMixin
    """
    left = root
    while left.children:
        left = left.children[0]
    return left


def rightmost(root: TreeType) -> TreeType:
    """
    Returns the rightmost leaf in this tree.

    :param d20.ast.ChildMixin root: The root node of the tree.
    :rtype: d20.ast.ChildMixin
    """
    right = root
    while right.children:
        right = right.children[-1]
    return right


def dfs(node: TreeType, predicate: Callable[[TreeType], bool]) -> Optional[TreeType]:
    """
    Returns the first node in the tree such that ``predicate(node)`` is True, searching depth-first left-to-right.
    Returns None if no node satisfying the predicate was found.

    :param d20.ast.ChildMixin node: The root node of the tree.
    :param predicate: A predicate function.
    :type predicate: Callable[[d20.ast.ChildMixin], bool]
    :rtype: Optional[d20.ast.ChildMixin]
    """
    if predicate(node):
        return node

    for child in node.children:
        result = dfs(child, predicate)
        if result is not None:
            return result

    return None
