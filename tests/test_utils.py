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


class TestTreeMap:
    def test_ast_map(self):
        tree = parse("1d20 + 4d6 + 3")

        def mapper(node):
            if isinstance(node, ast.Dice):
                node.num = node.num * 2
            return node

        mapped = utils.tree_map(mapper, tree)

        assert str(mapped) == '2d20 + 8d6 + 3'
        assert mapped is not tree
        assert str(tree) == '1d20 + 4d6 + 3'  # make sure it returned a copy

    def test_expr_map(self):
        expr = roll("1 + 2 + 3").expr

        def mapper(node):
            if isinstance(node, Literal):
                copied_values = node.values.copy()
                copied_values[-1] *= 2
                node.values = copied_values
            return node

        mapped = utils.tree_map(mapper, expr)

        assert SimpleStringifier().stringify(mapped) == '2 + 4 + 6 = 12'
        assert mapped.total == 12
        assert mapped is not expr
        assert SimpleStringifier().stringify(expr) == '1 + 2 + 3 = 6'


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
