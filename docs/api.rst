Class Reference
===============

Looking for information on :class:`d20.Expression` or :class:`d20.ast.Node`? Check out
:ref:`Expression Tree` for information on the Expression returned by a roll, or
:ref:`Abstract Syntax Tree` for the AST returned by a parse.

Dice
----
.. autoclass:: d20.Roller
    :members:

    .. attribute:: context
        :type: d20.RollContext

        The class used to track roll limits.

.. autoclass:: d20.RollResult
    :members:

    .. attribute:: ast
        :type: d20.ast.Node

        The abstract syntax tree of the dice expression that was rolled.

    .. attribute:: expr
        :type: d20.Expression

        The Expression representation of the result of the roll.

    .. attribute:: total
        :type: int

        The integer result of the roll (rounded towards 0).

    .. attribute:: result
        :type: str

        The string result of the roll. Equivalent to ``stringifier.stringify(self.expr)``.

    .. attribute:: comment
        :type: str or None

        If ``allow_comments`` was True and a comment was found, the comment. Otherwise, None.

.. autoclass:: d20.RollContext
    :members:

.. autoclass:: d20.AdvType
    :members:

    .. attribute:: NONE
        :type: int

        Equivalent to ``0``. Represents no advantage.

    .. attribute:: ADV
        :type: int

        Equivalent to ``1``. Represents advantage.

    .. attribute:: DIS
        :type: int

        Equivalent to ``-1``. Represents disadvantage.

.. autoclass:: d20.CritType
    :members:

    .. attribute:: NONE
        :type: int

        Equivalent to ``0``. Represents no crit.

    .. attribute:: CRIT
        :type: int

        Equivalent to ``1``. Represents a critical hit (a natural 20 on a d20).

    .. attribute:: FAIL
        :type: int

        Equivalent to ``2``. Represents a critical fail (a natural 1 on a d20).

Stringifiers
------------
.. autoclass:: d20.Stringifier

    .. automethod:: stringify

    .. automethod:: _stringify

    .. automethod:: _str_expression

    .. automethod:: _str_literal

    .. automethod:: _str_unop

    .. automethod:: _str_binop

    .. automethod:: _str_parenthetical

    .. automethod:: _str_set

    .. automethod:: _str_dice

    .. automethod:: _str_die

.. autoclass:: d20.SimpleStringifier

.. autoclass:: d20.MarkdownStringifier

Errors
------
.. autoclass:: d20.RollError
    :members:

.. autoclass:: d20.RollSyntaxError
    :members:

.. autoclass:: d20.RollValueError
    :members:

.. autoclass:: d20.TooManyRolls
    :members:
