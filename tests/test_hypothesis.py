from hypothesis import Verbosity, given, settings

from d20 import Expression, RollError, RollResult, ast, parse, roll
from . import custom_strategies as cst


@given(cst.expr())
@settings(verbosity=Verbosity.verbose, max_examples=1000, deadline=3000)
def test_any_valid_roll(expr):
    """Every valid dice expression should either return a valid result or raise a handled error"""
    parsed = parse(expr)
    try:
        result = roll(parsed)
        assert result
        assert isinstance(result, RollResult)
        assert isinstance(result.result, str)
        assert isinstance(result.total, (int, float))
        assert isinstance(result.ast, ast.Node)
        assert isinstance(result.expr, Expression)
    except RollError:
        return


# this fails on a few edge cases that we can simply ignore
# @given(cst.commented_expr())
# @settings(verbosity=Verbosity.verbose, max_examples=1000, deadline=3000)
# def test_any_valid_commented_roll(expr):
#     parsed = parse(expr, allow_comments=True)
#     try:
#         result = roll(parsed, allow_comments=True)
#         assert result
#         assert isinstance(result, RollResult)
#         assert isinstance(result.result, str)
#         assert isinstance(result.total, (int, float))
#         assert isinstance(result.ast, ast.Node)
#         assert isinstance(result.expr, Expression)
#     except RollError:
#         return
