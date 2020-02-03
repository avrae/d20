import copy

from d20 import diceast


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
