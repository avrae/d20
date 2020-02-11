import copy

from d20 import diceast, models


def ast_adv_copy(ast, advtype):
    """
    Returns a minimally shallow copy of a dice AST with respect to advantage.

    :param ast: The parsed AST.
    :type ast: d20.diceast.Node
    :param advtype: The advantage type to roll at.
    :type advtype: d20.AdvType
    :return: The copied AST.
    :rtype: d20.diceast.Node
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
    :type expr: d20.models.Number
    :param ambig_inherit: When encountering a child node with no annotation and the parent has ambiguous types, which to inherit. Can be None for no inherit, 'left' for leftmost, or 'right' for rightmost.
    :type ambig_inherit: Optional[Literal['left', 'right']]
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
        elif len(possible_types) and ambig_inherit is not None:
            for child in node.children:
                if child_possibilities[child]:
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
    :type expr: d20.models.Expression
    :param kwargs: Arguments that are passed to :func:`simplify_expr_annotations`.
    """
    simplify_expr_annotations(expr.roll, **kwargs)

    def do_simplify(node, first=False):
        """returns a pair of (replacement, branch had replacement)"""
        if node.annotation:
            return models.Literal(node.total, annotation=node.annotation), True

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
                replacement = models.Literal(child.total)
                node.set_child(i, replacement)

        return node, bool(had_replacement)

    do_simplify(expr, True)


if __name__ == '__main__':
    from d20 import roll, SimpleStringifier

    while True:
        expr = roll(input()).expr
        simplify_expr(expr)
        print(SimpleStringifier().stringify(expr))
