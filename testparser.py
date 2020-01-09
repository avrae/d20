"""
Test syntaxes:

1d20
1+1
4d6kh3
4*(3d8kh2+9[fire]+(9d2e2+3[cold])/2)
(1d4, 2+2, 3d6kl1)kh1
"""

from lark import Lark

with open("grammar.lark") as f:
    grammar = f.read()

parser = Lark(grammar, start='expr', parser='lalr')

while True:
    result = parser.parse(input())
    print(result.pretty())
    print(result)
