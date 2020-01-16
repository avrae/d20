import abc
import random
import diceast as ast


class Number(abc.ABC):  # num
    __slots__ = ("kept", "annotation")

    def __init__(self):
        self.kept = True
        self.annotation = None

    @property
    def number(self):
        """
        Returns the numerical value of this object.

        :rtype: int or float
        """
        return sum(n.number for n in self.keptset)

    @property
    def set(self):
        """
        Returns the set representation of this object.

        :rtype: list of Number
        """
        raise NotImplementedError

    @property
    def keptset(self):
        return [n for n in self.set if n.kept]

    def drop(self):
        self.kept = False

    def __int__(self):
        return int(self.number)

    def __float__(self):
        return float(self.number)

    def __str__(self):
        raise NotImplementedError


class Literal(Number):
    __slots__ = ("values", "exploded")

    def __init__(self, value):
        """
        :type value: int or float
        """
        super().__init__()
        self.values = [value]  # history is tracked to support mi/ma op
        self.exploded = False

    @property
    def number(self):
        return self.values[-1]

    @property
    def set(self):
        return [self]

    def explode(self):
        self.exploded = True

    def update(self, value):
        """
        :type value: int or float
        """
        self.values.append(value)

    def __str__(self):
        history = ' -> '.join(map(str, self.values))
        if self.exploded:
            return f"{history}!"
        return history


class UnOp(Number):
    __slots__ = ("op", "value")

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
        self.op = op
        self.value = value

    @property
    def number(self):
        return self.UNARY_OPS[self.op](self.value.number)

    @property
    def set(self):
        return [Literal(self.number)]

    def __str__(self):
        return f"{self.op}{str(self.value)}"


class BinOp(Number):
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

    def __init__(self, left, op, right):
        """
        :type op: str
        :type left: Number
        :type right: Number
        """
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    @property
    def number(self):
        return self.BINARY_OPS[self.op](self.left.number, self.right.number)

    @property
    def set(self):
        return [self.number]

    def __str__(self):
        return f"{str(self.left)} {self.op} {str(self.right)}"


class Parenthetical(Number):
    __slots__ = ("value", "operations")

    def __init__(self, value, operations=None):
        """
        :type value: Number
        :type operations: list of SetOperator
        """
        super().__init__()
        if operations is None:
            operations = []
        self.value = value
        self.operations = operations

    @property
    def number(self):
        return self.value.number

    @property
    def set(self):
        return self.value.set

    def __str__(self):
        return f"({str(self.value)}){''.join([str(op) for op in self.operations])}"


class Set(Number):
    __slots__ = ("values", "operations")

    def __init__(self, values, operations=None):
        """
        :type values: list of Number
        :type operations: list of SetOperator
        """
        super().__init__()
        if operations is None:
            operations = []
        self.values = values
        self.operations = operations

    @property
    def set(self):
        return self.values

    def __str__(self):
        out = f"{', '.join([str(v) for v in self.values])}"
        ops = ''.join([str(op) for op in self.operations])
        if len(self.values) == 1:
            return f"({out},){ops}"
        return f"({out}){ops}"


class Dice(Set):
    __slots__ = ("num", "size")

    def __init__(self, num, size, values, operations=None):
        """
        :type num: int
        :type size: int
        :type values: list of Die
        :type operations: list of SetOperator
        """
        super().__init__(values, operations)
        self.num = num
        self.size = size

    @classmethod
    def new(cls, num, size):
        return cls(num, size, [Die.new(size) for _ in range(num)], [])

    def roll_another(self):
        self.values.append(Die.new(self.size))

    def __str__(self):
        return f"{self.num}d{self.size}{''.join([str(op) for op in self.operations])} " \
               f"({', '.join([str(die) for die in self.values])})"


class Die(Number):  # part of diceexpr
    __slots__ = ("size", "values")

    def __init__(self, size, values):
        """
        :type size: int
        :type values: list of Literal
        """
        super().__init__()
        self.size = size
        self.values = values

    @classmethod
    def new(cls, size):
        inst = cls(size, [])
        inst._add_roll()
        return inst

    @property
    def number(self):
        return self.values[-1].number

    @property
    def set(self):
        return [self.values[-1]]

    def _add_roll(self):
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

    def __str__(self):
        return ", ".join([str(v) for v in self.values])


# noinspection PyUnresolvedReferences
# selecting on Dice will always return Die
class SetOperator:  # set_op, dice_op
    __slots__ = ("op", "sels")

    def __init__(self, op, sels):
        """
        :type op: str
        :type sels: list of SetSelector
        """
        self.op = op
        self.sels = sels

    @classmethod
    def from_ast(cls, node):
        return cls(node.op, [SetSelector.from_ast(n) for n in node.sels])

    def select(self, target):
        """
        :type target: Number
        """
        out = set()
        for selector in self.sels:
            out.update(selector.select(target))
        return out

    def operate(self, target):
        """
        Operates in place on the values in a base set.

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
        for die in self.select(target):
            die.explode()
            target.roll_another()

    def minimum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self.sels[-1]
        the_min = selector.num
        for die in target.values:
            if die.number < the_min:
                die.force_value(the_min)

    def maximum(self, target):  # immediate
        """
        :type target: Dice
        """
        selector = self.sels[-1]
        the_max = selector.num
        for die in target.values:
            if die.number > the_max:
                die.force_value(the_max)

    def __str__(self):
        return "".join([f"{self.op}{str(sel)}" for sel in self.sels])


class SetSelector:  # selector
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

    def select(self, target):
        """
        :type target: Number
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

        return set(selectors[self.cat](target))

    def lowestn(self, target):
        return sorted(target.keptset, key=lambda n: n.number)[:self.num]

    def highestn(self, target):
        return sorted(target.keptset, key=lambda n: n.number, reverse=True)[:self.num]

    def lessthan(self, target):
        return [n for n in target.keptset if n.number < self.num]

    def morethan(self, target):
        return [n for n in target.keptset if n.number > self.num]

    def literal(self, target):
        return [n for n in target.keptset if n.number == self.num]

    def __str__(self):
        if self.cat:
            return f"{self.cat}{self.num}"
        return str(self.num)


# ==== roller ====
# noinspection PyMethodMayBeStatic
class Roller:
    def __init__(self):
        self.nodes = {
            ast.Expression: self._eval_expression,
            ast.AnnotatedNumber: self._eval_annotatednumber,
            ast.Literal: self._eval_literal,
            ast.Parenthetical: self._eval_parenthetical,
            ast.UnOp: self._eval_unop,
            ast.BinOp: self._eval_binop,
            ast.OperatedSet: self._eval_operatedset,
            ast.NumberSet: self._eval_numberset,
            ast.OperatedDice: self._eval_operateddice,
            ast.Dice: self._eval_dice
        }

    def roll(self, expr):
        dice_tree = ast.parser.parse(expr)
        print(str(expr))
        result = self._eval(dice_tree)
        print(str(result))
        print(result.number)
        return result  # todo rollresult

    def _eval(self, node):
        handler = self.nodes[type(node)]
        return handler(node)

    def _eval_expression(self, node):
        return self._eval(node.roll)

    def _eval_annotatednumber(self, node):
        target = self._eval(node.value)
        target.annotation = ''.join(node.annotations)
        return target

    def _eval_literal(self, node):
        return Literal(node.value)

    def _eval_parenthetical(self, node):
        return Parenthetical(self._eval(node.value))

    def _eval_unop(self, node):
        return UnOp(node.op, self._eval(node.value))

    def _eval_binop(self, node):
        return BinOp(self._eval(node.left), node.op, self._eval(node.right))

    def _eval_operatedset(self, node):
        target = self._eval(node.value)
        for op in node.operations:
            the_op = SetOperator.from_ast(op)
            the_op.operate(target)
            target.operations.append(the_op)
        return target

    def _eval_numberset(self, node):
        return Set([self._eval(n) for n in node.values])

    def _eval_operateddice(self, node):
        return self._eval_operatedset(node)

    def _eval_dice(self, node):
        return Dice.new(node.num, node.size)


if __name__ == '__main__':
    roller = Roller()
    while True:
        roll_result = roller.roll(input())
