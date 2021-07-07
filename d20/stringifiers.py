import abc
from typing import Callable, Iterable, Mapping, Type, TypeVar

from .expression import *

__all__ = ("Stringifier", "SimpleStringifier", "MarkdownStringifier")

ExpressionNode = TypeVar('ExpressionNode', bound=Number)


class Stringifier(abc.ABC):
    """
    ABC for string builder from dice result.
    Children should implement all ``_str_*`` methods to transform an Expression into a str.
    """

    def __init__(self):
        self._nodes: Mapping[Type[ExpressionNode], Callable[[ExpressionNode], str]] = {
            Expression: self._str_expression,
            Literal: self._str_literal,
            UnOp: self._str_unop,
            BinOp: self._str_binop,
            Parenthetical: self._str_parenthetical,
            Set: self._str_set,
            Dice: self._str_dice,
            Die: self._str_die
        }

    def stringify(self, the_roll: ExpressionNode) -> str:
        """
        Transforms a rolled expression into a string recursively, bottom-up.

        :param the_roll: The expression to stringify.
        :type the_roll: d20.Expression
        :rtype: str
        """
        return self._stringify(the_roll)

    def _stringify(self, node: ExpressionNode) -> str:
        """
        Called on each node that needs to be stringified.

        :param node: The node to stringify.
        :type node: d20.Number
        :rtype: str
        """
        handler = self._nodes[type(node)]
        inside = handler(node)
        if node.annotation:
            return f"{inside} {node.annotation}"
        return inside

    def _str_expression(self, node: Expression) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Expression
        :rtype: str
        """
        raise NotImplementedError

    def _str_literal(self, node: Literal) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Literal
        :rtype: str
        """
        raise NotImplementedError

    def _str_unop(self, node: UnOp) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.UnOp
        :rtype: str
        """
        raise NotImplementedError

    def _str_binop(self, node: BinOp) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.BinOp
        :rtype: str
        """
        raise NotImplementedError

    def _str_parenthetical(self, node: Parenthetical) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Parenthetical
        :rtype: str
        """
        raise NotImplementedError

    def _str_set(self, node: Set) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Set
        :rtype: str
        """
        raise NotImplementedError

    def _str_dice(self, node: Dice) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Dice
        :rtype: str
        """
        raise NotImplementedError

    def _str_die(self, node: Die) -> str:
        """
        :param node: The node to stringify.
        :type node: d20.Die
        :rtype: str
        """
        raise NotImplementedError

    @staticmethod
    def _str_ops(operations: Iterable[SetOperator]) -> str:
        return ''.join([str(op) for op in operations])


class SimpleStringifier(Stringifier):
    """
    Example stringifier.
    """

    def _str_expression(self, node):
        return f"{self._stringify(node.roll)} = {int(node.total)}"

    def _str_literal(self, node):
        history = ' -> '.join(map(str, node.values))
        if node.exploded:
            return f"{history}!"
        return history

    def _str_unop(self, node):
        return f"{node.op}{self._stringify(node.value)}"

    def _str_binop(self, node):
        return f"{self._stringify(node.left)} {node.op} {self._stringify(node.right)}"

    def _str_parenthetical(self, node):
        return f"({self._stringify(node.value)}){self._str_ops(node.operations)}"

    def _str_set(self, node):
        out = f"{', '.join([self._stringify(v) for v in node.values])}"
        if len(node.values) == 1:
            return f"({out},){self._str_ops(node.operations)}"
        return f"({out}){self._str_ops(node.operations)}"

    def _str_dice(self, node):
        the_dice = [self._stringify(die) for die in node.values]
        return f"{node.num}d{node.size}{self._str_ops(node.operations)} ({', '.join(the_dice)})"

    def _str_die(self, node):
        the_rolls = [self._stringify(val) for val in node.values]
        return ', '.join(the_rolls)


class MarkdownStringifier(SimpleStringifier):
    """
    Transforms roll expressions into Markdown.
    """

    class _MDContext:
        def __init__(self):
            self.in_dropped = False

        def reset(self):
            self.in_dropped = False

    def __init__(self):
        super().__init__()
        self._context = self._MDContext()

    def stringify(self, the_roll):
        self._context.reset()
        return super().stringify(the_roll)

    def _stringify(self, node):
        if not node.kept and not self._context.in_dropped:
            self._context.in_dropped = True
            inside = super()._stringify(node)
            self._context.in_dropped = False
            return f"~~{inside}~~"
        return super()._stringify(node)

    def _str_expression(self, node):
        return f"{self._stringify(node.roll)} = `{int(node.total)}`"

    def _str_die(self, node):
        the_rolls = []
        for val in node.values:
            inside = self._stringify(val)
            if val.number == 1 or val.number == node.size:
                inside = f"**{inside}**"
            the_rolls.append(inside)
        return ', '.join(the_rolls)
