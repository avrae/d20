from lark import Lark

with open("grammar.lark") as f:
    grammar = f.read()

parser = Lark(grammar, start='expr', parser='lalr')

while True:
    result = parser.parse(input())
    print(result.pretty())
