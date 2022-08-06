"""
Custom Hypothesis strategies for property-based testing. This generally follows the grammar rules.
"""

from hypothesis import strategies as st


# rules
@st.composite
def expr(draw):
    return draw(num())


@st.composite
def commented_expr(draw):
    a = draw(num())
    b = draw(st.just("") | term_comment)
    return a + b


@st.composite
def num(draw):
    return draw(comparison())


@st.composite
def comparison(draw):
    elems = draw(st.lists(a_num(), min_size=1))
    if len(elems) > 1:
        op = draw(term_comp_operator)
        return op.join(elems)
    return elems[0]


@st.composite
def a_num(draw):
    elems = draw(st.lists(m_num(), min_size=1))
    if len(elems) > 1:
        op = draw(term_a_op)
        return op.join(elems)
    return elems[0]


@st.composite
def m_num(draw):
    elems = draw(st.lists(u_num(), min_size=1))
    if len(elems) > 1:
        op = draw(term_m_op)
        return op.join(elems)
    return elems[0]


@st.composite
def u_num(draw):
    @st.composite
    def recursive_step(draw_inner, b):
        a = draw_inner(term_u_op)
        return a + draw_inner(b)

    return draw(st.recursive(numexpr(), lambda e: recursive_step(e)))


@st.composite
def numexpr(draw):
    a = draw(dice() | rule_set() | literal())
    b = draw(st.lists(term_annotation).map("".join))
    return a + b


@st.composite
def literal(draw):
    return draw(term_integer | term_decimal)


@st.composite
def rule_set(draw):
    a = draw(setexpr())
    b = draw(st.lists(set_op()).map("".join))
    return a + b


@st.composite
def set_op(draw):
    a = draw(term_set_operator)
    b = draw(selector())
    return a + b


@st.composite
def setexpr(draw):
    elems = draw(st.lists(num(), min_size=1).map(", ".join))
    trailing_comma = draw(st.just("") | term_comma)
    return draw(st.just("()") | st.just("(" + elems + trailing_comma + ")"))


term_comma = st.just(",")  # idk why this is a rule, but it's here


@st.composite
def dice(draw, only_valid=True):
    a = draw(diceexpr(only_valid))
    b = draw(st.lists(dice_op()).map("".join))
    return a + b


@st.composite
def dice_op(draw):
    a = draw(term_dice_operator | term_set_operator)
    b = draw(selector())
    return a + b


@st.composite
def diceexpr(draw, only_valid=True):
    if only_valid:
        a = draw(st.just("") | st.integers(min_value=1, max_value=100).map(str))
        b = draw(st.integers(min_value=1).map(str) | st.just("%"))
    else:
        a = draw(st.just("") | term_integer)
        b = draw(term_dice_value)
    return a + "d" + b


@st.composite
def selector(draw):
    a = draw(st.just("") | term_seltype)
    b = draw(term_integer)
    return a + b


@st.composite
def annotation(draw):
    inner = draw(st.text(alphabet=st.characters(blacklist_characters="[]\n", blacklist_categories=("Cs",))))
    return "[" + inner + "]"


term_annotation = annotation()

# terminals
term_comment = st.text().map(lambda t: " " + t)  # any string starting w/ a space
term_comp_operator = st.sampled_from(("==", ">=", "<=", "!=", "<", ">"))
term_a_op = st.sampled_from("+-")
term_m_op = st.sampled_from(("*", "//", "/", "%"))
term_u_op = st.sampled_from("+-")
term_set_operator = st.sampled_from("kp")
term_dice_operator = st.sampled_from(("rr", "ro", "ra", "e", "mi", "ma"))
term_dice_value = st.integers(min_value=0).map(str) | st.just("%")
term_seltype = st.sampled_from("lh<>")
term_whitespace = st.text(alphabet="\t\f\r\n")
term_integer = st.integers(min_value=0).map(str)


# this is to make more draws succeed, since from_regex has a really aggressive filter
@st.composite
def decimal1(draw):
    a = draw(st.text(alphabet="0123456789", min_size=1))
    b = draw(st.text(alphabet="0123456789", min_size=0))
    return a + "." + b


@st.composite
def decimal2(draw):
    return "." + draw(st.text(alphabet="0123456789", min_size=1))


term_decimal = decimal1() | decimal2()
