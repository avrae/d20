import abc
import random

from . import diceast as ast
from . import errors

__all__ = (
    "Number", "Expression", "Literal", "UnOp", "BinOp", "Parenthetical", "Set", "Dice", "Die",
    "SetOperator", "SetSelector"
)


# ===== ast -> expression models =====
class Number(abc.ABC, ast.ChildMixin):  # num
    """
    The base class for all expression objects.

    Note that Numbers implement all the methods of a :class:`~d20.ast.ChildMixin`.
    """

    __slots__ = ("kept", "annotation")

    def __init__(self, kept=True, annotation=None):
        self.kept = kept
        self.annotation = annotation

    @property
    def number(self):
        """
        Returns the numerical value of this object.

        :rtype: int or float
        """
        return sum(n.number for n in self.keptset)

    @property
    def total(self):
        """
        Returns the numerical value of this object with respect to whether it's kept.
        Generally, this is preferred to use over ``number``, as this will return 0 if
        the number node was dropped.

        :rtype: int or float
        """
        return self.number if self.kept else 0

    @property
    def set(self):
        """
        Returns the set representation of this object.

        :rtype: list[Number]
        """
        raise NotImplementedError

    @property
    def keptset(self):
        """
        Returns the set representation of this object, but only including children whose values
        were not dropped.

        :rtype: list[Number]
        """
        return [n for n in self.set if n.kept]

    def drop(self):
        """
        Makes the value of this Number node not count towards a total.
        """
        self.kept = False

    def __int__(self):
        return int(self.total)

    def __float__(self):
        return float(self.total)

    def __repr__(self):
        return f"<Number total={self.total} kept={self.kept}>"

    # overridden methods for typechecking
    def set_child(self, index, value):
        """
        Sets the ith child of this Number.

        :param int index: Which child to set.
        :param value: The Number to set it to.
        :type value: Number
        """
        super().set_child(index, value)

    @property
    def children(self):
        """:rtype: list[Number]"""
        raise NotImplementedError


class Expression(Number):
    """Expressions are usually the root of all Number trees."""
    __slots__ = ("roll", "comment")

    def __init__(self, roll, comment, **kwargs):
        """
        :type roll: Number
        """
        super().__init__(**kwargs)
        self.roll = roll
        self.comment = comment

    @property
    def number(self):
        return self.roll.number

    @property
    def set(self):
        return self.roll.set

    @property
    def children(self):
        return [self.roll]

    def set_child(self, index, value):
        self._child_set_check(index)
        self.roll = value

    def __repr__(self):
        return f"<Expression roll={self.roll} comment={self.comment}>"


class Literal(Number):
    """A literal integer or float."""
    __slots__ = ("values", "exploded")

    def __init__(self, value, **kwargs):
        """
        :type value: int or float
        """
        super().__init__(**kwargs)
        self.values = [value]  # history is tracked to support mi/ma op
        self.exploded = False

    @property
    def number(self):
        return self.values[-1]

    @property
    def set(self):
        return [self]

    @property
    def children(self):
        return []

    def explode(self):
        self.exploded = True

    def update(self, value):
        """
        :type value: int or float
        """
        self.values.append(value)

    def __repr__(self):
        return f"<Literal {self.number}>"


class UnOp(Number):
    """Represents a unary operation."""
    __slots__ = ("op", "value")

    UNARY_OPS = {
        "-": lambda v: -v,
        "+": lambda v: +v
    }

    def __init__(self, op, value, **kwargs):
        """
        :type op: str
        :type value: Number
        """
        super().__init__(**kwargs)
        self.op = op
        self.value = value

    @property
    def number(self):
        return self.UNARY_OPS[self.op](self.value.total)

    @property
    def set(self):
        return [self]

    @property
    def children(self):
        return [self.value]

    def set_child(self, index, value):
        self._child_set_check(index)
        self.value = value

    def __repr__(self):
        return f"<UnOp op={self.op} value={self.value}>"


class BinOp(Number):
    """Represents a binary operation."""
    __slots__ = ("op", "left", "right")

    BINARY_OPS = {
        "+": lambda l, r: l + r,
        "-": lambda l, r: l - r,
        "*": lambda l, r: l * r,
        "/": lambda l, r: l / r,
        "//": lambda l, r: l // r,
        "%": lambda l, r: l % r,
        "<": lambda l, r: int(l < r),
        ">": lambda l, r: int(l > r),
        "==": lambda l, r: int(l == r),
        ">=": lambda l, r: int(l >= r),
        "<=": lambda l, r: int(l <= r),
        "!=": lambda l, r: int(l != r),
    }

    def __init__(self, left, op, right, **kwargs):
        """
        :type op: str
        :type left: Number
        :type right: Number
        """
        super().__init__(**kwargs)
        self.op = op
        self.left = left
        self.right = right

    @property
    def number(self):
        try:
            return self.BINARY_OPS[self.op](self.left.total, self.right.total)
        except ZeroDivisionError:
            raise errors.RollValueError("Cannot divide by zero.")

    @property
    def set(self):
        return [self]

    @property
    def children(self):
        return [self.left, self.right]

    def set_child(self, index, value):
        self._child_set_check(index)
        if self.children[index] is self.left:
            self.left = value
        else:
            self.right = value

    def __repr__(self):
        return f"<BinOp left={self.left} op={self.op} right={self.right}>"


class Parenthetical(Number):
    """Represents a value inside parentheses."""
    __slots__ = ("value", "operations")

    def __init__(self, value, operations=None, **kwargs):
        """
        :type value: Number
        :type operations: list[SetOperator]
        """
        super().__init__(**kwargs)
        if operations is None:
            operations = []
        self.value = value
        self.operations = operations

    @property
    def total(self):
        return self.value.total if self.kept else 0

    @property
    def set(self):
        return self.value.set

    @property
    def children(self):
        return [self.value]

    def set_child(self, index, value):
        self._child_set_check(index)
        self.value = value

    def __repr__(self):
        return f"<Parenthetical value={self.value} operations={self.operations}>"


class Set(Number):
    """Represents a set of values."""
    __slots__ = ("values", "operations")

    def __init__(self, values, operations=None, **kwargs):
        """
        :type values: list[Number]
        :type operations: list[SetOperator]
        """
        super().__init__(**kwargs)
        if operations is None:
            operations = []
        self.values = values
        self.operations = operations

    @property
    def set(self):
        return self.values

    @property
    def children(self):
        return self.values

    def set_child(self, index, value):
        self._child_set_check(index)
        self.values[index] = value

    def __repr__(self):
        return f"<Set values={self.values} operations={self.operations}>"

    def __copy__(self):
        return Set(values=self.values.copy(), operations=self.operations.copy())


class Dice(Set):
    """A set of Die."""
    __slots__ = ("num", "size", "_context")

    def __init__(self, num, size, values, operations=None, context=None, **kwargs):
        """
        :type num: int
        :type size: int|str
        :type values: list of Die
        :type operations: list[SetOperator]
        :type context: dice.RollContext
        """
        super().__init__(values, operations, **kwargs)
        self.num = num
        self.size = size
        self._context = context

    @classmethod
    def new(cls, num, size, context=None):
        return cls(num, size, [Die.new(size, context=context) for _ in range(num)], context=context)

    def roll_another(self):
        self.values.append(Die.new(self.size, context=self._context))

    @property
    def children(self):
        return []

    def __repr__(self):
        return f"<Dice num={self.num} size={self.size} values={self.values} operations={self.operations}>"

    def __copy__(self):
        return Dice(num=self.num, size=self.size, context=self._context,
                    values=self.values.copy(), operations=self.operations.copy(), )


class Die(Number):  # part of diceexpr
    """Represents a single die."""
    __slots__ = ("size", "values", "_context")

    def __init__(self, size, values, context=None):
        """
        :type size: int
        :type values: list of Literal
        :type context: dice.RollContext
        """
        super().__init__()
        self.size = size
        self.values = values
        self._context = context

    @classmethod
    def new(cls, size, context=None):
        inst = cls(size, [], context=context)
        inst._add_roll()
        return inst

    @property
    def number(self):
        return self.values[-1].total

    @property
    def set(self):
        return [self.values[-1]]

    @property
    def children(self):
        return []

    def _add_roll(self):
        if self.size != '%' and self.size < 1:
            raise errors.RollValueError("Cannot roll a 0-sided die.")
        if self._context:
            self._context.count_roll()
        if self.size == '%':
            n = Literal(random.randrange(0, 100, 10))
        else:
            n = Literal(random.randrange(self.size) + 1)  # 200ns faster than randint(1, self._size)
        self.values.append(n)

    def reroll(self):
        if self.values:
            self.values[-1].drop()
        self._add_roll()

    def explode(self):
        if self.values:
            self.values[-1].explode()
        # another Die is added by the explode operator

    def force_value(self, new_value):
        if self.values:
            self.values[-1].update(new_value)

    def __repr__(self):
        return f"<Die size={self.size} values={self.values}>"


# noinspection PyUnresolvedReferences
# selecting on Dice will always return Die
class SetOperator:  # set_op, dice_op
    """Represents an operation on a set."""
    __slots__ = ("op", "sels")

    def __init__(self, op, sels):
        """
        :type op: str
        :type sels: list[SetSelector]
        """
        self.op = op
        self.sels = sels

    @classmethod
    def from_ast(cls, node):
        return cls(node.op, [SetSelector.from_ast(n) for n in node.sels])

    def select(self, target, max_targets=None):
        """
        Selects the operands in a target set.

        :param target: The source of the operands.
        :type target: Number
        :param max_targets: The maximum number of targets to select.
        :type max_targets: Optional[int]
        """
        out = set()
        for selector in self.sels:
            batch_max = None
            if max_targets is not None:
                batch_max = max_targets - len(out)
                if batch_max == 0:
                    break

            out.update(selector.select(target, max_targets=batch_max))
        return out

    def operate(self, target):
        """
        Operates in place on the values in a target set.

        :param target: The source of the operands.
        :type target: Number
        """
        operations = {
            "k": self.keep,
            "p": self.drop,
            # dice only
            "rr": self.reroll,
            "ro": self.reroll_once,
            "ra": self.explode_once,
            "e": self.explode,
            "mi": self.minimum,
            "ma": self.maximum
        }

        operations[self.op](target)

    def keep(self, target):
        """
        :type target: Set
        """
        for value in target.keptset:
            if value not in self.select(target):
                value.drop()

    def drop(self, target):
        """
        :type target: Set
        """
        for value in self.select(target):
            value.drop()

    def reroll(self, target):
        """
        :type target: Dice
        """
        to_reroll = self.select(target)
        while to_reroll:
            for die in to_reroll:
                die.reroll()

            to_reroll = self.select(target)

    def reroll_once(self, target):
        """
        :type target: Dice
        """
        for die in self.select(target):
            die.reroll()

    def explode(self, target):
        """
        :type target: Dice
        """
        to_explode = self.select(target)
        already_exploded = set()

        while to_explode:
            for die in to_explode:
                die.explode()
                target.roll_another()

            already_exploded.update(to_explode)
            to_explode = self.select(target).difference(already_exploded)

    def explode_once(self, target):
        """
        :type target: Dice
        """
        for die in self.select(target, max_targets=1):
            die.explode()
            target.roll_another()

    def minimum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self.sels[-1]
        if selector.cat is not None:
            raise errors.RollValueError(f"{str(selector)} is not a valid selector for minimums.")
        the_min = selector.num
        for die in target.keptset:
            if die.number < the_min:
                die.force_value(the_min)

    def maximum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self.sels[-1]
        if selector.cat is not None:
            raise errors.RollValueError(f"{str(selector)} is not a valid selector for maximums.")
        the_max = selector.num
        for die in target.keptset:
            if die.number > the_max:
                die.force_value(the_max)

    def __str__(self):
        return "".join([f"{self.op}{str(sel)}" for sel in self.sels])

    def __repr__(self):
        return f"<SetOperator op={self.op} sels={self.sels}>"


class SetSelector:  # selector
    """Represents a selection on a set."""
    __slots__ = ("cat", "num")

    def __init__(self, cat, num):
        """
        :type cat: str or None
        :type num: int
        """
        self.cat = cat
        self.num = num

    @classmethod
    def from_ast(cls, node):
        return cls(node.cat, node.num)

    def select(self, target, max_targets=None):
        """
        Selects operands from a target set.

        :param target: The source of the operands.
        :type target: Number
        :param int max_targets: The maximum number of targets to select.
        :return: The targets in the set.
        :rtype: set of Number
        """
        selectors = {
            "l": self.lowestn,
            "h": self.highestn,
            "<": self.lessthan,
            ">": self.morethan,
            None: self.literal
        }

        selected = selectors[self.cat](target)
        if max_targets is not None:
            selected = selected[:max_targets]
        return set(selected)

    def lowestn(self, target):
        return sorted(target.keptset, key=lambda n: n.total)[:self.num]

    def highestn(self, target):
        return sorted(target.keptset, key=lambda n: n.total, reverse=True)[:self.num]

    def lessthan(self, target):
        return [n for n in target.keptset if n.total < self.num]

    def morethan(self, target):
        return [n for n in target.keptset if n.total > self.num]

    def literal(self, target):
        return [n for n in target.keptset if n.total == self.num]

    def __str__(self):
        if self.cat:
            return f"{self.cat}{self.num}"
        return str(self.num)

    def __repr__(self):
        return f"<SetSelector cat={self.cat} num={self.num}>"
