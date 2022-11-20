import pytest

from d20 import *

STANDARD_EXPRESSIONS = [
    "1d20",
    "1d%",
    "1+1",
    "4d6kh3",
    "(1)",
    "(1,)",
    "((1d6))",
    "4*(3d8kh2+9[fire]+(9d2e2+3[cold])/2)",
    "(1d4, 2+2, 3d6kl1)kh1",
    "((10d6kh5)kl2)kh1",
]


def r(e):
    return roll(e).total  # I'm tired of typing roll a bunch of times


# high level tests
def test_rolls_dont_error():
    for expr in STANDARD_EXPRESSIONS:
        assert roll(expr)


def test_roll_types():
    for expr in STANDARD_EXPRESSIONS:
        result = roll(expr)
        assert isinstance(result, RollResult)
        assert isinstance(result.result, str)
        assert isinstance(result.total, (int, float))
        assert isinstance(result.ast, ast.Node)
        assert isinstance(result.expr, Expression)


def test_sane_totals():
    for _ in range(1000):
        assert 1 <= r("1d20") <= 20
        assert 0 <= r("1d%") <= 90
        assert 0 <= r("1d%") % 10 <= 9
        assert r("1d%") % 10 == 0
        assert 3 <= r("4d6kh3") <= 18
        assert 1 <= r("(((1d6)))") <= 6
        assert 4 <= r("(1d4, 2+2, 3d6kl1)kh1") <= 6
        assert 1 <= r("((10d6kh5)kl2)kh1") <= 6


def test_pemdas():
    assert r("1 + 3 * 6") == r("1 + (3 * 6)") == 19
    assert r("(1 + 3) * 6") == 24
    assert r("1 + 2 + 3") == r("(1 + 2) + 3") == r("1 + (2 + 3)") == 6
    assert r("1 + 2 == 2") == 0
    assert r("1 + (2 == 2)") == 2


def test_invalid_rolls():
    with pytest.raises(TooManyRolls):
        r("1001d6")
    with pytest.raises(RollValueError):
        r("6d0")
    with pytest.raises(RollValueError):
        r("10d6mil1")


def test_chaining_operators():
    assert 0 <= r("10d6k1k2k3") <= 30
    assert 0 <= r("10d6k1ph1") <= 9
    assert r("(1, 2, 3)k1k2") == 3


def test_crit():
    # roll until we get a crit
    result = roll("1d20")
    while result.total != 20:
        result = roll("1d20")
    assert result.crit == CritType.CRIT

    while result.total != 1:
        result = roll("1d20")
    assert result.crit == CritType.FAIL

    while result.total == 1 or result.total == 20:
        result = roll("1d20")
    assert result.crit == CritType.NONE


# node tests
def test_literal():
    assert r("1") == 1
    assert r("10000") == 10000
    assert r("1.5") == 1
    assert r("0.5") == r(".5") == 0


def test_dice():
    for _ in range(1000):
        assert r("0d6") == 0
        assert 1 <= r("d6") <= 6
        assert 1 <= r("1d6") <= 6
        assert 2 <= r("2d6") <= 12
        assert r("0d%") == 0
        assert 0 <= r("d%") <= 90
        assert 0 <= r("1d%") <= 90
        assert 0 <= r("2d%") <= 180


def test_set():
    assert r("(1)") == 1
    assert r("(1,)") == 1
    assert r("(1, 1)") == 2


def test_unop():
    assert r("1") == r("+1") == 1
    assert r("-1") == -1
    assert r("--1") == 1  # double negative
    assert r("-+-++---+1") == -1  # I mean, I guess


def test_binop():
    assert r("2 + 2") == 4
    assert r("2 - 2") == 0
    assert r("2 * 5") == 10
    assert r("15 / 2") == 7
    assert r("15 // 2") == 7
    assert r("13 % 2") == 1


def test_binop_dice():
    for _ in range(1000):
        assert 3 <= r("2 + 1d6") <= 8
        assert 2 <= r("2 * 1d6") <= 12
        assert r("60 / 1d6") in [60, 30, 20, 15, 12, 10]
        assert r("60 // 1d6") in [60, 30, 20, 15, 12, 10]
        assert r("1d100 % 10") <= 10
        assert r("1d% % 10") <= 10


def test_div_zero():
    with pytest.raises(RollValueError):
        r("10 / 0")
    with pytest.raises(RollValueError):
        r("10 // 0")
    with pytest.raises(RollValueError):
        r("10 % 0")


def test_comparison():
    assert r("1 == 1") == 1
    assert r("1 == 2") == 0
    assert r("1 > 1") == 0
    assert r("2 > 1") == 1
    assert r("1 < 1") == 0
    assert r("1 < 2") == 1
    assert r("1 >= 1") == 1
    assert r("1 >= 2") == 0
    assert r("1 <= 1") == 1
    assert r("2 <= 1") == 0
    assert r("1 != 1") == 0
    assert r("1 != 2") == 1


def test_selectors():
    assert r("(1, 2, 3, 4, 5)k3") == 3
    assert r("(1, 2, 3, 4, 5)k<3") == 3
    assert r("(1, 2, 3, 4, 5)k>3") == 9
    assert r("(1, 2, 3, 4, 5)kl2") == 3
    assert r("(1, 2, 3, 4, 5)kh2") == 9
    assert r("(1)k1") == 1
    assert r("(1)k2") == 0


# set operators
def test_k_op():
    assert r("(1, 2, 3, 4, 5)k3") == 3
    assert r("(1, 2, 3, 4, 5)k1k2") == 3
    assert r("(1, 2, 3, 4, 5)kh1kl1") == 6


def test_p_op():
    assert r("(1, 2, 3, 4, 5)p3") == 12
    assert r("(1, 2, 3, 4, 5)p1p2") == 12
    assert r("(1, 2, 3, 4, 5)ph1pl1") == 9


# dice operators
def test_rr_op():
    assert r("1d20rr<20") == 20
    assert r("1d20rr>1") == 1
    with pytest.raises(TooManyRolls):
        r("1d20rr<21")
    with pytest.raises(TooManyRolls):
        r("1d1rr1")


def test_ro_op():
    assert r("1d1ro1") == 1
    assert 1 <= r("1d6rol1") <= 6


def test_ra_op():
    assert r("1d1ra1") == 2
    assert 2 <= r("1d6ral1") <= 12


def test_e_op():
    assert r("1d2e2") % 2 == 1
    with pytest.raises(TooManyRolls):
        r("1d20e<21")
    with pytest.raises(TooManyRolls):
        r("1d1e1")


def test_mi_op():
    assert r("10d6mi6") == 60
    assert r("10d6mi10") == 100
    assert 20 <= r("10d6mi2") <= 60


def test_ma_op():
    assert r("10d6ma1") == 10
    assert r("10d6ma0") == 0
    assert 10 <= r("10d6ma5") <= 50


# modifying the tree directly
def test_correct_results():
    result = roll("1+2+3")
    assert result.total == 6
    assert result.result == "1 + 2 + 3 = `6`"
    result.expr.roll = BinOp(result.expr.roll, "+", Literal(4))
    assert result.total == 10
    assert result.result == "1 + 2 + 3 + 4 = `10`"
