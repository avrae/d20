import copy
import re

from d20 import *


class TestAstAdvCopy:
    def test_adv(self):
        for expr in ("1d20", "1d20+1", "d20-1d4"):
            tree = parse(expr)
            original_tree = copy.deepcopy(tree)

            adv_tree = utils.ast_adv_copy(tree, AdvType.ADV)
            assert str(adv_tree).startswith("2d20kh1")
            assert str(adv_tree) != str(original_tree)

            adv_tree = utils.ast_adv_copy(tree, AdvType.DIS)
            assert str(adv_tree).startswith("2d20kl1")
            assert str(adv_tree) != str(original_tree)

            adv_tree = utils.ast_adv_copy(tree, AdvType.NONE)
            assert str(adv_tree).startswith("1d20")
            assert str(adv_tree) == str(original_tree)

    def test_not_applicable(self):
        for expr in ("1", "1d6", "1+1"):
            tree = parse(expr)
            original_tree = copy.deepcopy(tree)

            adv_tree = utils.ast_adv_copy(tree, AdvType.ADV)
            assert str(adv_tree) == str(original_tree)

    def test_copy(self):
        for expr in ("1d20", "1d20ro1"):
            tree = parse(expr)
            adv_tree = utils.ast_adv_copy(tree, AdvType.ADV)

            assert tree is not adv_tree
            assert str(adv_tree) != str(tree)
            assert str(parse(expr)) == str(tree)


def test_annotation_simplify():
    expr = roll("1 [a] + 2 + 3 [b] + 4").expr
    utils.simplify_expr_annotations(expr, None)
    assert SimpleStringifier().stringify(expr) == "1 + 2 [a] + 3 [b] + 4 = 10"

    expr = roll("1 [a] + 2 + 3 [b] + 4").expr
    utils.simplify_expr_annotations(expr, 'left')
    assert SimpleStringifier().stringify(expr) == "1 + 2 [a] + 3 [b] + 4 [a] = 10"

    expr = roll("1 [a] + 2 + 3 [b] + 4").expr
    utils.simplify_expr_annotations(expr, 'right')
    assert SimpleStringifier().stringify(expr) == "1 + 2 [a] + 3 [b] + 4 [b] = 10"


def test_simplify():
    expr = roll("1 [a] + 2 + 3 [b] + 4").expr
    utils.simplify_expr(expr)
    assert SimpleStringifier().stringify(expr) == "3 [a] + 3 [b] + 4 = 10"

    expr = roll("1 [a] + 2 + 3").expr
    utils.simplify_expr(expr)
    assert SimpleStringifier().stringify(expr) == "6 [a] = 6"

    expr = roll("1 + 2 + 3 + 4").expr
    utils.simplify_expr(expr)
    assert SimpleStringifier().stringify(expr) == "10 = 10"

    expr = roll("8d6").expr
    utils.simplify_expr(expr)
    assert re.match(r"(\d+) = \1", SimpleStringifier().stringify(expr))

    expr = roll("8d6 [fire]").expr
    utils.simplify_expr(expr)
    assert re.match(r"(\d+) \[fire\] = \1", SimpleStringifier().stringify(expr))
