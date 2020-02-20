Abstract Syntax Tree
====================

This page documents the structure of the Expression object as returned by ``parse(...)``. If you're looking
for the Expression object returned by ``roll(...)expr``, check out :ref:`Expression Tree`.

.. autoclass:: d20.ast.ChildMixin

    .. method:: children
        :property:

        (read-only) The children of this object, usually used for traversing a tree.

        :rtype: list[Node]

    .. method:: left
        :property:

        The leftmost child of this object, usually used for traversing a tree.

        :rtype: Node

    .. method:: right
        :property:

        The rightmost child of this object, usually used for traversing a tree..

        :rtype: Node

    .. automethod:: set_child

.. autoclass:: d20.ast.Node
    :show-inheritance:

.. autoclass:: d20.ast.Expression
    :show-inheritance:

    .. attribute:: roll
        :type: d20.ast.Node

        The subtree representing the expression's roll.

    .. attribute:: comment
        :type: Optional[str]

        The comment of this expression.

.. autoclass:: d20.ast.AnnotatedNumber
    :show-inheritance:

    .. attribute:: value
        :type: d20.ast.Node

        The subtree representing the annotated value.

    .. attribute:: annotations
        :type: list[str]

        The annotations on the value.

.. autoclass:: d20.ast.Literal
    :show-inheritance:

    .. attribute:: value
        :type: Union[int, float]

        The literal number represented.

.. autoclass:: d20.ast.Parenthetical
    :show-inheritance:

    .. attribute:: value
        :type: d20.ast.Node

        The subtree inside the parentheses.

.. autoclass:: d20.ast.UnOp
    :show-inheritance:

    .. attribute:: op
        :type: str

        The unary operation.

    .. attribute:: value
        :type: d20.ast.Node

        The subtree that the operation operates on.

.. autoclass:: d20.ast.BinOp
    :show-inheritance:

    .. attribute:: op
        :type: str

        The binary operation.

    .. attribute:: left
        :type: d20.ast.Node

        The left subtree that the operation operates on.

    .. attribute:: right
        :type: d20.ast.Node

        The right subtree that the operation operates on.

.. autoclass:: d20.ast.OperatedSet
    :show-inheritance:

    .. attribute:: value
        :type: d20.ast.NumberSet

        The set to be operated on.

    .. attribute:: operations
        :type: list[d20.SetOperation]

        The operations to run on the set.

.. autoclass:: d20.ast.NumberSet
    :show-inheritance:

    .. attribute:: values
        :type: list[d20.ast.NumberSet]

        The elements of the set.

.. autoclass:: d20.ast.OperatedDice
    :show-inheritance:

.. autoclass:: d20.ast.Dice
    :show-inheritance:

    .. attribute:: num
        :type: int

        The number of dice to roll.

    .. attribute:: size
        :type: int

        How many sides each die should have.

.. autoclass:: d20.ast.SetOperator

    .. attribute:: op
        :type: str

        The operation to run on the selected elements of the set.

    .. attribute:: sels
        :type: list[d20.SetSelector]

        The selectors that describe how to select operands.

.. autoclass:: d20.ast.SetSelector

    .. attribute:: cat
        :type: Optional[str]

        The type of selection (lowest, highest, literal, etc).

    .. attribute:: num
        :type: int

        The number to select (the N in lowest/highest/etc N, or literally N).

