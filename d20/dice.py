from enum import IntEnum

from . import diceast as ast
from .errors import *
from .models import *
from .stringifiers import MarkdownStringifier

__all__ = ("CritType", "RollContext", "RollResult", "Roller")


class CritType(IntEnum):
    NORMAL = 0
    CRIT = 1
    FAIL = 2


class RollContext:
    def __init__(self, max_rolls=1000):
        self.max_rolls = max_rolls
        self.rolls = 0
        self.reset()

    def reset(self):
        self.rolls = 0

    def count_roll(self, n=1):
        self.rolls += n
        if self.rolls > self.max_rolls:
            raise TooManyRolls("Too many dice rolled.")


class RollResult:
    def __init__(self, the_ast, the_roll, stringifier):
        """
        :type the_ast: ast.Node
        :type the_roll: models.Expression
        :type stringifier: stringifiers.Stringifier
        """
        self.ast = the_ast
        self.roll = the_roll
        self.total = the_roll.total
        self.result = stringifier.stringify(the_roll)
        self.comment = the_roll.comment

    @property
    def crit(self):
        """
        If the leftmost node was Xd20kh1, returns :type:`CritType.CRIT` if the roll was a 20 and
        :type:`CritType.FAIL` if the roll was a 1.
        Returns :type:`CritType.NORMAL` otherwise.

        :rtype: CritType
        """
        # find the left most node in the dice expression
        left = self.roll
        while left.children:
            left = left.children[0]

        # ensure the node is dice
        if not isinstance(left, Dice):
            return CritType.NORMAL

        # ensure only one die of size 20 is kept
        if not (len(left.keptset) == 1 and left.size == 20):
            return CritType.NORMAL

        if left.total == 1:
            return CritType.FAIL
        elif left.total == 20:
            return CritType.CRIT
        return CritType.NORMAL

    def __str__(self):
        return self.result

    def __repr__(self):
        return f"<RollResult total={self.total}>"


# noinspection PyMethodMayBeStatic
class Roller:
    def __init__(self):
        self._nodes = {
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
        self.context = RollContext()

    def roll(self, expr, stringifier=None):
        """
        Rolls the dice.

        :param expr: The dice to roll.
        :type expr: str or ast.Node
        :param stringifier: The stringifier to stringify the result. Defaults to MarkdownStringifier.
        :type stringifier: stringifiers.Stringifier
        :rtype: RollResult
        """
        if stringifier is None:
            stringifier = MarkdownStringifier()

        self.context.reset()
        dice_tree = ast.parser.parse(expr)
        dice_expr = self._eval(dice_tree)
        return RollResult(dice_tree, dice_expr, stringifier)

    def _eval(self, node):
        # noinspection PyUnresolvedReferences
        # for some reason pycharm thinks this isn't a valid dict operation
        handler = self._nodes[type(node)]
        return handler(node)

    def _eval_expression(self, node):
        return Expression(self._eval(node.roll), node.comment)

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
        return Dice.new(node.num, node.size, context=self.context)


if __name__ == '__main__':
    roller = Roller()
    while True:
        roll_result = roller.roll(input())
        print(str(roll_result))
        print(roll_result.crit)
