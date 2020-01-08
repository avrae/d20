import abc
import random


class Number(abc.ABC):
    @property
    def numval(self):
        """Returns the numerical value of this object."""
        raise NotImplementedError


class Literal(Number):
    def __init__(self, value):
        """
        :type value: int or float
        """
        self._value = value

    @property
    def numval(self):
        return self._value


class UnOp(Number):
    pass  # todo - does this even need to be a class?


class BinOp(Number):
    pass  # todo


class NumberSet(Number):
    def __init__(self, values):
        """
        :type values: list of Number
        """
        self._values = values

    @property
    def numval(self):
        return sum(n.numval for n in self._values)


class Dice(NumberSet):
    def __init__(self, values):
        """
        :type values: list of Die
        """
        super().__init__(values)

    @classmethod
    def new(cls, num, size):
        return cls([Die.new(size) for _ in range(num)])


class Die(Number):
    def __init__(self, size, values):
        self._size = size
        self._rolled_values = values

    @classmethod
    def new(cls, size):
        return cls(size, [])

    @property
    def numval(self):
        if not self._rolled_values:
            self.roll()
        return self._rolled_values[-1]

    def roll(self):
        self._rolled_values.append(random.randrange(self._size) + 1)  # 200ns faster than randint(1, self._size)
