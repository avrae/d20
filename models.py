import abc
import random


class Expression:  # expr
    __slots__ = ("roll", "comment")

    def __init__(self, roll, comment=None):
        self.roll = roll
        self.comment = comment


class Number(abc.ABC):  # num
    __slots__ = ("_kept",)

    def __init__(self):
        self._kept = True

    @property
    def numval(self):
        """Returns the numerical value of this object."""
        raise NotImplementedError

    @property
    def kept(self):
        return self._kept

    def drop(self):
        self._kept = False

    def __int__(self):
        return int(self.numval)

    def __float__(self):
        return float(self.numval)


class AnnotatedNumber(Number):  # numexpr
    __slots__ = ("_value", "_annotations")

    def __init__(self, value, *annotations):
        """
        :type value: Number
        :type annotations: str
        """
        super().__init__()
        self._value = value
        self._annotations = annotations

    @property
    def numval(self):
        return self._value.numval


class Literal(Number):  # literal
    __slots__ = ("_values", "_exploded")

    def __init__(self, value):
        """
        :type value: int or float
        """
        super().__init__()
        self._values = [value]  # history is tracked to support mi/ma op
        self._exploded = False

    @property
    def numval(self):
        return self._values[-1]

    def explode(self):
        self._exploded = True

    def update(self, value):
        """
        :type value: int or float
        """
        self._values.append(value)


class UnOp(Number):  # u_num
    __slots__ = ("_op", "_value")

    UNARY_OPS = {
        "-": lambda v: -v,
        "+": lambda v: +v
    }

    def __init__(self, op, value):
        """
        :type op: str
        :type value: Number
        """
        super().__init__()
        self._op = op
        self._value = value

    @property
    def numval(self):
        return self.UNARY_OPS[self._op](self._value.numval)


class BinOp(Number):  # a_num, m_num
    __slots__ = ("_op", "_left", "_right")

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

    def __init__(self, left, op, right):
        """
        :type op: str
        :type left: Number
        :type right: Number
        """
        super().__init__()
        self._op = op
        self._left = left
        self._right = right

    @property
    def numval(self):
        return self.BINARY_OPS[self._op](self._left.numval, self._right.numval)


# noinspection PyUnresolvedReferences
# selecting on Dice will always return Die
class SetOperator:  # set_op, dice_op
    __slots__ = ("_op", "_sels")

    IMMEDIATE = {"mi", "ma"}

    def __init__(self, op, sels):
        """
        :type op: str
        :type sels: list of SetSelector
        """
        self._op = op
        self._sels = sels

    @classmethod
    def new(cls, op, sel):
        return cls(op, [sel])

    def add_sels(self, sels):
        self._sels.extend(sels)

    @property
    def op(self):
        return self._op

    @property
    def sels(self):
        return self._sels

    def select(self, target):
        """
        :type target: NumberSet
        """
        out = set()
        for selector in self._sels:
            out.update(selector.select(target))
        return out

    def operate(self, target):
        """
        Operates in place on the values in a base set.

        :type target: NumberSet
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

        operations[self._op](target)

    def keep(self, target):
        """
        :type target: NumberSet
        """
        for value in target.keptvalues:
            if value not in self.select(target):
                value.drop()

    def drop(self, target):
        """
        :type target: NumberSet
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
        for die in self.select(target):
            die.explode()
            target.roll_another()

    def minimum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self._sels[-1]
        the_min = selector.num
        for die in target.values:
            if die.numval < the_min:
                die.force_value(the_min)

    def maximum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self._sels[-1]
        the_max = selector.num
        for die in target.values:
            if die.numval > the_max:
                die.force_value(the_max)


class SetSelector:  # selector
    __slots__ = ("_cat", "_num")

    def __init__(self, cat, num):
        """
        :type cat: str or None
        :type num: int
        """
        self._cat = cat
        self._num = num

    @property
    def cat(self):
        return self._cat

    @property
    def num(self):
        return self._num

    def select(self, target):
        """
        :type target: NumberSet
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

        return set(selectors[self._cat](target))

    def lowestn(self, target):
        return sorted(target.keptvalues, key=lambda n: n.numval)[:self._num]

    def highestn(self, target):
        return sorted(target.keptvalues, key=lambda n: n.numval, reverse=True)[:self._num]

    def lessthan(self, target):
        return [n for n in target.keptvalues if n.numval < self._num]

    def morethan(self, target):
        return [n for n in target.keptvalues if n.numval > self._num]

    def literal(self, target):
        return [n for n in target.keptvalues if n.numval == self._num]


class OperatedSet(Number):  # set
    __slots__ = ("_value", "_operations", "_final")

    def __init__(self, the_set, *operations, final=False):
        """
        :type the_set: NumberSet
        :type operations: SetOperator
        :type final: bool
        """
        super().__init__()
        self._value = the_set
        self._operations = operations
        self._final = final

    @property
    def numval(self):
        if not self._final:
            self.run_ops()
        return self._value.numval

    def _simplify_operations(self):
        """Simplifies expressions like k1k2k3 into k(1,2,3)."""
        new_operations = []

        for operation in self._operations:
            if operation.op in SetOperator.IMMEDIATE or not new_operations:
                new_operations.append(operation)
            else:
                last_op = new_operations[-1]
                if operation.op == last_op.op:
                    last_op.add_sels(operation.sels)
                else:
                    new_operations.append(operation)

        self._operations = new_operations

    def run_ops(self):
        self._simplify_operations()

        for op in self._operations:
            op.operate(self._value)
        self._final = True


class NumberSet(Number):  # setexpr
    __slots__ = ("_values",)

    def __init__(self, *values):
        """
        :type values: Number
        """
        super().__init__()
        self._values = list(values)

    @property
    def numval(self):
        return sum(n.numval for n in self._values if n.kept)

    @property
    def values(self):
        return self._values

    @property
    def keptvalues(self):
        return [n for n in self.values if n.kept]


class OperatedDice(OperatedSet):  # dice
    __slots__ = ()

    def __init__(self, the_set, *operations, final=False):
        """
        :type the_set: Dice
        :type operations: SetOperator
        :type final: bool
        """
        super().__init__(the_set, *operations, final=final)


class Dice(NumberSet):  # diceexpr
    __slots__ = ("_num", "_size")

    def __init__(self, num, size, *values):
        """
        :type num: int
        :type size: int
        :type values: Die
        """
        super().__init__(*values)
        self._num = num
        self._size = size

    @classmethod
    def new(cls, num, size):
        return cls(num, size, *[Die.new(size) for _ in range(num)])

    def roll_another(self):
        self._values.append(Die.new(self._size))


class Die(Number):  # part of diceexpr
    __slots__ = ("_size", "_rolled_values")

    def __init__(self, size, values):
        """
        :type size: int
        :type values: list of Literal
        """
        super().__init__()
        self._size = size
        self._rolled_values = values

    @classmethod
    def new(cls, size):
        return cls(size, [])

    @property
    def numval(self):
        if not self._rolled_values:
            self._add_roll()
        return self._rolled_values[-1].numval

    def _add_roll(self):
        n = Literal(random.randrange(self._size) + 1)  # 200ns faster than randint(1, self._size)
        self._rolled_values.append(n)

    def reroll(self):
        if self._rolled_values:
            self._rolled_values[-1].drop()
        self._add_roll()

    def explode(self):
        if self._rolled_values:
            self._rolled_values[-1].explode()
        # another Die is added by the explode operator

    def force_value(self, new_value):
        if self._rolled_values:
            self._rolled_values[-1].update(new_value)
