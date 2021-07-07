from enum import IntEnum
from typing import Callable, Mapping, MutableMapping, Optional, Type, TypeVar, Union

import cachetools
import lark

from . import diceast as ast, utils
from .errors import *
from .expression import *
from .stringifiers import MarkdownStringifier, Stringifier

__all__ = ("CritType", "AdvType", "RollContext", "RollResult", "Roller")

POSSIBLE_COMMENT_AMBIGUITIES = {"*", }

TreeType = TypeVar('TreeType', bound=ast.ChildMixin)
ASTNode = TypeVar('ASTNode', bound=ast.Node)
ExpressionNode = TypeVar('ExpressionNode', bound=Number)


class CritType(IntEnum):
    """
    Integer enumeration representing the crit type of a roll.
    """
    NONE = 0
    CRIT = 1
    FAIL = 2


class AdvType(IntEnum):
    """
    Integer enumeration representing at what advantage a roll should be made at.
    """
    NONE = 0
    ADV = 1
    DIS = -1


class RollContext:
    """
    A class to track information about rolls to ensure all rolls halt eventually.

    To use this class, pass an instance to the constructor of :class:`d20.Roller`.
    """

    def __init__(self, max_rolls=1000):
        self.max_rolls = max_rolls
        self.rolls = 0
        self.reset()

    def reset(self):
        """Called at the start of each new roll."""
        self.rolls = 0

    def count_roll(self, n=1):
        """
        Called each time a die is about to be rolled.

        :param int n: The number of rolls about to be made.
        :raises d20.TooManyRolls: if the roller should stop rolling dice because too many have been rolled.
        """
        self.rolls += n
        if self.rolls > self.max_rolls:
            raise TooManyRolls("Too many dice rolled.")


class RollResult:
    """
    Holds information about the result of a roll. This should generally not be constructed manually.
    """

    def __init__(self, the_ast: ASTNode, the_roll: Expression, stringifier: Stringifier):
        """
        :type the_ast: ast.Node
        :type the_roll: d20.Expression
        :type stringifier: d20.Stringifier
        """
        self.ast = the_ast
        self.expr = the_roll
        self.stringifier = stringifier
        self.comment = the_roll.comment

    @property
    def total(self) -> int:
        return int(self.expr.total)

    @property
    def result(self) -> str:
        return self.stringifier.stringify(self.expr)

    @property
    def crit(self) -> CritType:
        """
        If the leftmost node was Xd20kh1, returns :class:`CritType.CRIT` if the roll was a 20 and
        :class:`CritType.FAIL` if the roll was a 1.
        Returns :class:`CritType.NONE` otherwise.

        :rtype: CritType
        """
        # find the left most node in the dice expression
        left = self.expr
        while left.children:
            left = left.children[0]

        # ensure the node is dice
        if not isinstance(left, Dice):
            return CritType.NONE

        # ensure only one die of size 20 is kept
        if not (len(left.keptset) == 1 and left.size == 20):
            return CritType.NONE

        if left.total == 1:
            return CritType.FAIL
        elif left.total == 20:
            return CritType.CRIT
        return CritType.NONE

    def __str__(self):
        return self.result

    def __int__(self):
        return self.total

    def __float__(self):
        return self.expr.total

    def __repr__(self):
        return f"<RollResult total={self.total}>"


# noinspection PyMethodMayBeStatic
class Roller:
    """The main class responsible for parsing dice into an AST and evaluating that AST."""

    def __init__(self, context: Optional[RollContext] = None):
        if context is None:
            context = RollContext()

        self._nodes: Mapping[Type[ASTNode], Callable[[ASTNode], ExpressionNode]] = {
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
        self._parse_cache: MutableMapping[str, ASTNode] = cachetools.LFUCache(256)
        self.context: RollContext = context

    def roll(self,
             expr: Union[str, ASTNode],
             stringifier: Optional[Stringifier] = None,
             allow_comments: bool = False,
             advantage: AdvType = AdvType.NONE) -> RollResult:
        """
        Rolls the dice.

        :param expr: The dice to roll.
        :type expr: str or ast.Node
        :param stringifier: The stringifier to stringify the result. Defaults to MarkdownStringifier.
        :type stringifier: d20.Stringifier
        :param bool allow_comments: Whether to parse for comments after the main roll expression (potential slowdown)
        :param AdvType advantage: If the roll should be made at advantage. Only applies if the leftmost node is 1d20.
        :rtype: RollResult
        """
        if stringifier is None:
            stringifier = MarkdownStringifier()

        self.context.reset()

        if isinstance(expr, str):  # is this a preparsed tree?
            dice_tree = self.parse(expr, allow_comments)
        else:
            dice_tree = expr

        if advantage != AdvType.NONE:
            dice_tree = utils.ast_adv_copy(dice_tree, advantage)

        dice_expr = self._eval(dice_tree)
        return RollResult(dice_tree, dice_expr, stringifier)

    # parsers
    def parse(self, expr: str, allow_comments: bool = False) -> ast.Expression:
        """
        Parses a dice expression into an AST.

        :param expr: The dice to roll.
        :type expr: str
        :param bool allow_comments: Whether to parse for comments after the main roll expression (potential slowdown)
        :rtype: ast.Expression
        """
        try:
            if not allow_comments:
                return self._parse_no_comment(expr)
            else:
                return self._parse_with_comments(expr)
        except lark.UnexpectedToken as ut:
            raise RollSyntaxError(ut.line, ut.column, ut.token, ut.expected)
        except lark.UnexpectedCharacters as uc:
            raise RollSyntaxError(uc.line, uc.column, expr[uc.pos_in_stream], uc.allowed)

    def _parse_no_comment(self, expr: str) -> ast.Expression:
        # see if this expr is in cache
        clean_expr = expr.replace(' ', '')
        if clean_expr in self._parse_cache:
            return self._parse_cache[clean_expr]
        dice_tree = ast.parser.parse(expr, start='expr')
        self._parse_cache[clean_expr] = dice_tree
        return dice_tree

    def _parse_with_comments(self, expr: str) -> ast.Expression:
        try:
            return ast.parser.parse(expr, start='commented_expr')
        except lark.UnexpectedInput as ui:
            # if the statement up to the unexpected token ends with an operator, remove that from the end
            successful_fragment = expr[:ui.pos_in_stream]
            for op in POSSIBLE_COMMENT_AMBIGUITIES:
                if successful_fragment.endswith(op):
                    successful_fragment = successful_fragment[:-len(op)]
                    force_comment = expr[len(successful_fragment):]
                    break
            else:
                raise
            # and parse again (handles edge cases like "1d20 keep the dragon grappled")
            result = ast.parser.parse(successful_fragment, start='commented_expr')
            result.comment = force_comment
            return result

    # evaluator
    def _eval(self, node: ASTNode) -> ExpressionNode:
        # noinspection PyUnresolvedReferences
        # for some reason pycharm thinks this isn't a valid dict operation
        handler = self._nodes[type(node)]
        return handler(node)

    def _eval_expression(self, node: ast.Expression) -> Expression:
        return Expression(self._eval(node.roll), node.comment)

    def _eval_annotatednumber(self, node: ast.AnnotatedNumber) -> ExpressionNode:
        target = self._eval(node.value)
        target.annotation = ''.join(node.annotations)
        return target

    def _eval_literal(self, node: ast.Literal) -> Literal:
        return Literal(node.value)

    def _eval_parenthetical(self, node: ast.Parenthetical) -> Parenthetical:
        return Parenthetical(self._eval(node.value))

    def _eval_unop(self, node: ast.UnOp) -> UnOp:
        return UnOp(node.op, self._eval(node.value))

    def _eval_binop(self, node: ast.BinOp) -> BinOp:
        return BinOp(self._eval(node.left), node.op, self._eval(node.right))

    def _eval_operatedset(self, node: ast.OperatedSet) -> ExpressionNode:
        target = self._eval(node.value)
        for op in node.operations:
            the_op = SetOperator.from_ast(op)
            the_op.operate(target)
            target.operations.append(the_op)
        return target

    def _eval_numberset(self, node: ast.NumberSet) -> Set:
        return Set([self._eval(n) for n in node.values])

    def _eval_operateddice(self, node: ast.OperatedDice) -> ExpressionNode:
        return self._eval_operatedset(node)

    def _eval_dice(self, node: ast.Dice) -> Dice:
        return Dice.new(node.num, node.size, context=self.context)
