from lark import Discard, Lark, Transformer

from models import *


class RollTransformer(Transformer):
    COMMENT = str
    COMP_OPERATOR = str
    A_OP = str
    M_OP = str
    U_OP = str
    ANNOTATION = str
    OPERATOR = str
    DICE_OPERATOR = str
    SELTYPE = str
    INTEGER = int
    DECIMAL = float

    def expr(self, num_comment):
        return Expression(*num_comment)

    def par_num(self, num):
        return Parenthetical(*num)

    def comparison(self, binop):
        return BinOp(*binop)

    def a_num(self, binop):
        return BinOp(*binop)

    def m_num(self, binop):
        return BinOp(*binop)

    def u_num(self, unop):
        return UnOp(*unop)

    def numexpr(self, num_anno):
        return AnnotatedNumber(*num_anno)

    def literal(self, num):
        return Literal(*num)

    def set(self, opset):
        return OperatedSet(*opset)

    def set_op(self, opsel):
        return SetOperator.new(*opsel)

    def setexpr(self, the_set):
        return NumberSet(the_set)

    def dice(self, opdice):
        return OperatedDice(*opdice)

    def dice_op(self, opsel):
        return SetOperator.new(*opsel)

    def diceexpr(self, dice):
        if len(dice) == 1:
            return Dice.new(1, *dice)
        return Dice.new(*dice)

    def selector(self, sel):
        if len(sel) == 1:
            return SetSelector(None, *sel)
        return SetSelector(*sel)


if __name__ == '__main__':
    with open("grammar.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, start='expr', parser='lalr')

    while True:
        result = parser.parse(input())
        print(result.pretty())
        print(result)
        out = RollTransformer(visit_tokens=True).transform(result)
        print(out.roll.numval)
        print(str(out))
