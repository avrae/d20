# d20

[![PyPI version shields.io](https://img.shields.io/pypi/v/d20.svg)](https://pypi.python.org/pypi/d20/)
[![PyPI license](https://img.shields.io/pypi/l/d20.svg)](https://pypi.python.org/pypi/d20/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/d20.svg)](https://pypi.python.org/pypi/d20/)
![](https://github.com/avrae/d20/workflows/Test%20Package/badge.svg)



A fast, powerful, and extensible dice engine for D&D, d20 systems, and any other system that needs dice!

## Key Features
- Quick to start - just use `d20.roll()`!
- Optimized for speed and memory efficiency
- Highly extensible API for custom behaviour and dice stringification
- Built-in execution limits against malicious dice expressions
- Tree-based dice representation for easy traversal 

## Installing
**Requires Python 3.6+**.

```
python3 -m pip install -U d20
```

## Quickstart

```python
>>> import d20
>>> result = d20.roll("1d20+5")
>>> str(result)
'1d20 (10) + 5 = `15`'
>>> result.total
15
>>> result.crit
<CritType.NORMAL: 0>
>>> str(result.ast)
'1d20 + 5'
```

## Dice Syntax
This is the grammar supported by the dice parser, roughly ordered in how tightly the grammar binds.

### Numbers
These are the atoms used at the base of the syntax tree.

| Name    | Syntax            | Description       | Examples           |
|---------|-------------------|-------------------|--------------------|
| literal | `INT`, `DECIMAL`  | A literal number. | `1`, `0.5`, `3.14` |
| dice    | `INT? "d" INT`    | A set of die.     | `d20`, `3d6`       |
| set     | `"(" (num ("," num)* ","?)? ")"` | A set of expressions. | `()`, `(2,)`, `(1, 3+3, 1d20)` |

Note that `(3d6)` is equivalent to `3d6`, but `(3d6,)` is the set containing the one element `3d6`.

### Set Operations
These operations can be performed on dice and sets.

#### Grammar
| Name    | Syntax            | Description       | Examples           |
|---------|-------------------|-------------------|--------------------|
| set_op  | `operation selector` | An operation on a set (see below). | `kh3`, `ro<3` |
| selector | `seltype INT` | A selection on a set (see below). | `3`, `h1`, `>2` |

#### Operators
Operators are always followed by a selector, and operate on the items in the set that match the selector.

| Syntax | Name | Description |
|---|---|---|
| k | keep | Keeps all matched values. |
| p | drop | Drops all matched values. |
| rr | reroll | Rerolls all matched values until none match. (Dice only) |
| ro | reroll once | Rerolls all matched values once. (Dice only) |
| ra | reroll and add | Rerolls all matched values once, keeping the original roll. (Dice only) |
| e | explode on | Rolls another die for each matched value. (Dice only) |
| mi | minimum | Sets the minimum value of each die. (Dice only) |
| ma | maximum | Sets the maximum value of each die. (Dice only) |

#### Selectors
Selectors select from the remaining kept values in a set.

| Syntax | Name | Description |
|---|---|---|
| X | literal | All values in this set that are literally this value. |
| hX | highest X | The highest X values in the set. |
| lX | lowest X | The lowest X values in the set. |
| \>X | greater than X | All values in this set greater than X. |
| <X | less than X | All values in this set less than X. |

### Unary Operations
| Syntax | Name | Description |
|---|---|---|
| +X | positive | Does nothing. |
| -X | negative | The negative value of X. |

### Binary Operations
| Syntax | Name |
|---|---|
| X * Y | multiplication |
| X / Y | division |
| X // Y | int division |
| X % Y | modulo |
| X + Y | addition |
| X - Y | subtraction |
| X == Y | equality |
| X >= Y | greater/equal |
| X <= Y | less/equal |
| X > Y | greater than |
| X < Y | less than |
| X != Y | inequality |

### Examples
```python
>>> from d20 import roll
>>> r = roll("4d6kh3")  # highest 3 of 4 6-sided dice
>>> r.total
14
>>> str(r)
'4d6kh3 (4, 4, **6**, ~~3~~) = `14`'

>>> r = roll("2d6ro<3")  # roll 2d6s, then reroll any 1s or 2s once
>>> r.total
9
>>> str(r)
'2d6ro<3 (**~~1~~**, 3, **6**) = `9`'

>>> r = roll("8d6mi2")  # roll 8d6s, with each die having a minimum roll of 2
>>> r.total
33
>>> str(r)
'8d6mi2 (1 -> 2, **6**, 4, 2, **6**, 2, 5, **6**) = `33`'
```

## Custom Stringifier
By default, d20 stringifies the result of each dice roll formatted in Markdown, which may not be useful in your application. 
To change this behaviour, you can create a subclass of [`d20.Stringifier`](https://github.com/avrae/d20/blob/master/d20/stringifiers.py) 
(or `d20.SimpleStringifier` as a starting point), and implement the `_str_*` methods to customize how your dice tree is stringified. 

Then, simply pass an instance of your stringifier into the `roll()` function!
```python
>>> import d20
>>> class MyStringifier(d20.SimpleStringifier):
...     def _stringify(self, node):
...         if not node.kept:
...             return 'X'
...         return super()._stringify(node)
...
...     def _str_expression(self, node):
...         return f"The result of the roll {self._stringify(node.roll)} was {int(node.total)}"

>>> result = d20.roll("4d6e6kh3", stringifier=MyStringifier())
>>> str(result)
'The result of the roll 4d6e6kh3 (X, 5, 6!, 6!, X, X) was 17'
```

## Annotations and Comments
Each dice node supports value annotations - i.e., a method to "tag" parts of a roll with some indicator. For example,
```
3d6 [fire] + 1d4 [piercing]
-(1d8 + 3) [healing]
(1 [one], 2 [two], 3 [three])
```
are all examples of valid annotations. Annotations are purely visual and do not affect the evaluation of the roll by default.

Additionally, when `allow_comments=True` is passed to `roll()`, the result of the roll may have a comment:
```python
>>> from d20 import roll
>>> result = roll("1d20 I rolled a d20", allow_comments=True)
>>> str(result)
'1d20 (13) = `13`'
>>> result.comment
'I rolled a d20'
```
Note that while `allow_comments` is enabled, AST caching is disabled, which may lead to slightly worse performance.


## Documentation

TODO