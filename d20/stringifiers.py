import abc

from .models import *

__all__ = ("Stringifier", "SimpleStringifier", "MarkdownStringifier")


class Stringifier(abc.ABC):
    """
    ABC for string builder from dice result.
    Children should implement all ``_str_*`` methods to transform an Expression into a str.
    """

    def __init__(self):
        self._nodes = {
            Expression: self._str_expression,
            Literal: self._str_literal,
            UnOp: self._str_unop,
            BinOp: self._str_binop,
            Parenthetical: self._str_parenthetical,
            Set: self._str_set,
            Dice: self._str_dice,
            Die: self._str_die
        }

    def stringify(self, the_roll):
        """
        Transforms a rolled expression into a string.

        :type the_roll: models.Expression
        :rtype: str
        """
        return self._stringify(the_roll)

    def _stringify(self, node):
        handler = self._nodes[type(node)]
        inside = handler(node)
        if node.annotation:
            return f"{inside} {node.annotation}"
        return inside

    def _str_expression(self, node):
        raise NotImplementedError

    def _str_literal(self, node):
        raise NotImplementedError

    def _str_unop(self, node):
        raise NotImplementedError

    def _str_binop(self, node):
        raise NotImplementedError

    def _str_parenthetical(self, node):
        raise NotImplementedError

    def _str_set(self, node):
        raise NotImplementedError

    def _str_dice(self, node):
        raise NotImplementedError

    def _str_die(self, node):
        raise NotImplementedError

    @staticmethod
    def _str_ops(operations):
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
