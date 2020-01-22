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

d20 is built on top of the amazing [Lark](https://github.com/lark-parser/lark) parser, and has it as its only dependency!

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

## Documentation

TODO