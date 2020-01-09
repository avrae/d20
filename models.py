import abc
import random


class Number(abc.ABC):  # num
    @property
    def numval(self):
        """Returns the numerical value of this object."""
        raise NotImplementedError

    def __int__(self):
        return int(self.numval)

    def __float__(self):
        return float(self.numval)


class AnnotatedNumber(Number):  # numexpr
    def __init__(self, value, *annotations):
        """
        :type value: Number
        :type annotations: str
        """
        self._value = value
        self._annotations = annotations

    @property
    def numval(self):
        return self._value.numval


class Literal(Number):  # literal
    def __init__(self, value):
        """
        :type value: int or float
        """
        self._value = value

    @property
    def numval(self):
        return self._value


class UnOp(Number):  # u_num
    UNARY_OPS = {
        "-": lambda v: -v,
        "+": lambda v: +v
    }

    def __init__(self, op, value):
        """
        :type op: str
        :type value: Number
        """
        self._op = op
        self._value = value

    @property
    def numval(self):
        return self.UNARY_OPS[self._op](self._value.numval)


class BinOp(Number):  # a_num, m_num
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
        self._op = op
        self._left = left
        self._right = right


class SetOperator:  # set_op, dice_op
    def __init__(self, op, sel):
        self._op = op
        self._sel = sel


class SetSelector:  # selector
    def __init__(self, cat, num):
        self._cat = cat
        self._num = num


class OperatedSet(Number):  # set
    def __init__(self, the_set, *operations, final=False):
        """
        :type the_set: NumberSet
        :type operations: SetOperator
        :type final: bool
        """
        self._value = the_set
        self._operations = operations
        self._final = final

    @property
    def numval(self):
        if not self._final:
            self.run_ops()
        return self._value.numval

    def run_ops(self):
        raise NotImplementedError  # todo


class NumberSet(Number):  # setexpr
    def __init__(self, values):
        """
        :type values: list of Number
        """
        self._values = values

    @property
    def numval(self):
        return sum(n.numval for n in self._values)


class OperatedDice(OperatedSet):  # dice
    def __init__(self, the_set, *operations, final=False):
        """
        :type the_set: Dice
        :type operations: SetOperator
        :type final: bool
        """
        super().__init__(the_set, *operations, final=final)

    def run_ops(self):
        raise NotImplementedError  # todo


class Dice(NumberSet):  # diceexpr
    def __init__(self, values):
        """
        :type values: list of Die
        """
        super().__init__(values)

    @classmethod
    def new(cls, num, size):
        return cls([Die.new(size) for _ in range(num)])


class Die(Number):  # part of diceexpr
    def __init__(self, size, values):
        """
        :type size: int
        :type values: list of Literal
        """
        self._size = size
        self._rolled_values = values

    @classmethod
    def new(cls, size):
        return cls(size, [])

    @property
    def numval(self):
        if not self._rolled_values:
            self.roll()
        return self._rolled_values[-1].numval

    def roll(self):
        n = Literal(random.randrange(self._size) + 1)  # 200ns faster than randint(1, self._size)
        self._rolled_values.append(n)
