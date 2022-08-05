"""
Utility to check out the dice tree and generate images of graphs because pretty.

Test syntaxes:

1d20
1+1
4d6kh3
(1)
(1,)
(((1d6)))
4*(3d8kh2+9[fire]+(9d2e2+3[cold])/2)
(1d4, 2+2, 3d6kl1)kh1
((10d6kh5)kl2)kh1
"""

from lark import Lark
from lark.tree import pydot__tree_to_png

with open("d20/grammar.lark") as f:
    grammar = f.read()

parser = Lark(grammar, start="expr", parser="lalr")

while True:
    result = parser.parse(input())
    print(result.pretty())
    print(result)
    pydot__tree_to_png(result, "tree.png")
