import copy

from d20 import diceast, expression


def ast_adv_copy(ast, advtype):
    """
    Returns a minimally shallow copy of a dice AST with respect to advantage.

    >>> tree = parse("1d20 + 5")
    >>> str(tree)
    '1d20 + 5'
    >>> str(ast_adv_copy(tree, AdvType.ADV))
    '2d20kh1 + 5'

    :param ast: The parsed AST.
    :type ast: d20.ast.Node
    :param advtype: The advantage type to roll at.
    :type advtype: d20.AdvType
    :return: The copied AST.
    :rtype: d20.ast.Node
    """
    root = copy.copy(ast)
    if not advtype:
        return root

    # find the leftmost node, making shallow copies all the way down
    parent = None
    child = root
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


def simplify_expr_annotations(expr, ambig_inherit=None):
    """
    Transforms an expression in place by simplifying the annotations using a bubble-up method.

    >>> expr = roll("1d20[foo]+3").expr
    >>> simplify_expr_annotations(expr.roll)
    >>> SimpleStringifier().stringify(expr)
    "1d20 (4) + 3 [foo] = 7"

    :param expr: The expression to transform.
    :type expr: d20.Number
    :param ambig_inherit: When encountering a child node with no annotation and the parent has ambiguous types, which \
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


def simplify_expr(expr, **kwargs):
    """
    Transforms an expression in place by simplifying it (removing all dice and evaluating branches with respect to annotations).

    >>> expr = roll("1d20[foo] + 3 - 1d4[bar]").expr
    >>> simplify_expr(expr)
    >>> SimpleStringifier().stringify(expr)
    "7 [foo] - 2 [bar] = 5"

    :param expr: The expression to transform.
    :type expr: d20.Expression
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


def tree_map(func, node):
    """
    Returns a copy of the tree, with each node replaced with ``func(node)``.

    :param func: A transformer function.
    :type func: typing.Callable[[d20.ast.ChildMixin], d20.ast.ChildMixin]
    :param node: The root of the tree to transform.
    :type node: d20.ast.ChildMixin
    """
    copied = copy.copy(node)
    for i, child in enumerate(copied.children):
        copied.set_child(i, tree_map(func, child))
    return func(copied)


def leftmost(root):
    """
    Returns the leftmost leaf in this tree.

    :param root: The root node of the tree.
    :type root: d20.ast.ChildMixin
    :rtype: d20.ast.ChildMixin
    """
    left = root
    while left.children:
        left = left.children[0]
    return left


def rightmost(root):
    """
    Returns the rightmost leaf in this tree.

    :param root: The root node of the tree.
    :type root: d20.ast.ChildMixin
    :rtype: d20.ast.ChildMixin
    """
    right = root
    while right.children:
        right = right.children[-1]
    return right


def dfs(node, predicate):
    """
    Returns the first node in the tree such that ``predicate(node)`` is True, searching depth-first left-to-right.

    :param node: The root node of the tree.
    :type node: d20.ast.ChildMixin
    :param predicate: A predicate function.
    :type predicate: typing.Callable[[d20.ast.ChildMixin], bool]
    :rtype: d20.ast.ChildMixin
    """
    if predicate(node):
        return node

    for child in node.children:
        result = dfs(child, predicate)
        if result is not None:
            return result

    return None
