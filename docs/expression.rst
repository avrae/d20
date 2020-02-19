Expression Tree
===============

This page documents the structure of the Expression object as returned by ``roll(...).expr``. If you're looking
for the Expression object returned by ``parse(...)``, check out :ref:`Abstract Syntax Tree`.


.. autoclass:: d20.Number
    :members: number, total, set, keptset, drop

    .. attribute:: kept
        :type: bool

        Whether this Number was kept or dropped in the final calculation.

    .. attribute:: annotation
        :type: Optional[str]

        The annotation on this Number, if any.

    .. method:: children
        :property:

        (read-only) The children of this Number, usually used for traversing the expression tree.

        :rtype: list[Number]

    .. method:: left
        :property:

        The leftmost child of this Number, usually used for traversing the expression tree.

        :rtype: Number

    .. method:: right
        :property:

        The rightmost child of this Number, usually used for traversing the expression tree.

        :rtype: Number

    .. automethod:: set_child

.. autoclass:: d20.Expression
    :show-inheritance:

    .. attribute:: roll
        :type: d20.Number

        The roll of this expression.

    .. attribute:: comment
        :type: Optional[str]

        The comment of this expression.

.. autoclass:: d20.Literal
    :show-inheritance:

    .. attribute:: values
        :type: list[Union[int, float]]

        The history of numbers that this literal has been.

    .. attribute:: exploded
        :type: bool

        Whether this literal was a value in a :class:`~d20.Die` object that caused it to explode.

    .. method:: explode()

        Marks that this literal was a value in a :class:`~d20.Die` object that caused it to explode.

    .. method:: update(value)

        Changes the literal value this literal represents.

        :param value: The new value.
        :type value: Union[int, float]

.. autoclass:: d20.UnOp
    :show-inheritance:

    .. attribute:: op
        :type: str

        The unary operation.

    .. attribute:: value
        :type: d20.Number

        The subtree that the operation operates on.

.. autoclass:: d20.BinOp
    :show-inheritance:

    .. attribute:: op
        :type: str

        The binary operation.

    .. attribute:: left
        :type: d20.Number

        The left subtree that the operation operates on.

    .. attribute:: right
        :type: d20.Number

        The right subtree that the operation operates on.

.. autoclass:: d20.Parenthetical
    :show-inheritance:

    .. attribute:: value
        :type: d20.Number

        The subtree inside the parentheses.

    .. attribute:: operations
        :type: list[d20.SetOperation]

        If the value inside the parentheses is a :class:`~d20.Set`, the operations to run on it.

.. autoclass:: d20.Set
    :show-inheritance:

    .. attribute:: values
        :type: list[d20.Number]

        The elements of the set.

    .. attribute:: operations
        :type: list[d20.SetOperation]

        The operations to run on the set.

.. autoclass:: d20.Dice
    :show-inheritance:

    .. attribute:: num
        :type: int

        How many :class:`~d20.Die` in this set of dice.

    .. attribute:: size
        :type: int

        The size of each :class:`~d20.Die` in this set of dice.

    .. attribute:: values
        :type: list[d20.Die]

        The elements of the set.

    .. attribute:: operations
        :type: list[d20.SetOperation]

        The operations to run on the set.

    .. method:: roll_another()

        Rolls another :class:`~d20.Die` of the appropriate size and adds it to this set.

.. autoclass:: d20.Die
    :show-inheritance:

    .. attribute:: size
        :type: int

        How many sides this Die has.

    .. attribute:: values
        :type: list[d20.Literal]

        The history of values this die has rolled.

.. autoclass:: d20.SetOperator

    .. attribute:: op
        :type: str

        The operation to run on the selected elements of the set.

    .. attribute:: sels
        :type: list[d20.SetSelector]

        The selectors that describe how to select operands.

    .. automethod:: select

    .. automethod:: operate

.. autoclass:: d20.SetSelector

    .. attribute:: cat
        :type: Optional[str]

        The type of selection (lowest, highest, literal, etc).

    .. attribute:: num
        :type: int

        The number to select (the N in lowest/highest/etc N, or literally N).

    .. automethod:: select
