---
title: "AoC 2017 Day 24: Maker Of Bridges"
date: 2017-12-24
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2017
---
### Source: [Electromagnetic Moat](http://adventofcode.com/2017/day/24)

> **Part 1:** Given a series of reversible components of the form `3/4` (can connect a `3` on one end to a `4` on the other), form a bridge of components. The bridge's strength is equal to the sum of component values. So `0/3, 3/7, and 7/4` has a strength of `0+3 + 3+7 + 7+4 = 24`.

> What is the strongest possible bridge?

<!--more-->

Let's just brute force it. What I want to do is write a function that will take a list of components and (recursively) generate a list of all possible bridges:

```python
Bridge = collections.namedtuple('Bridge', 'strength length components')

components = frozenset(
    tuple(map(int, line.split('/')))
    for line in lib.input()
)

@functools.lru_cache(None)
def bridges(connector, components):
    '''Return all bridges that can be constructed from this point.'''

    for component in components:
        x, y = component
        if x == connector or y == connector:
            for strength, length, bridge in bridges(y if x == connector else x, components - {component}):
                yield Bridge(
                    strength + x + y,
                    length + 1,
                    [(x, y)] + bridge
                )

    yield Bridge(0, 0, [])
```

That's actually pretty cool. Basically, as long as we have a few components left, we're going to take every possible component that could be next (either way) and make a bridge from it. To make that bridge, we recursively look at all components *but* that one, and make a bridge of those. Since the number of remaining components is always getting smaller, this function is guaranteed to return.

Since the first component of the returned tuple is the strength, we can find the strongest bridge with `max`:

```python
print(max(
    bridges(0, components),
))
```

> **Part 2:** What is the strength of the *longest* bridge you can make (break ties with the strongest)?

For this, we just need to sort by a different field. We'll sort by `length` and break ties with the full `Bridge` (thus `strength`):

```python
lib.add_argument('--sort-by', required = True, choices = ('strength', 'length'))

print(max(
    bridges(0, components),
    key = lambda bridge: (getattr(bridge, lib.param('sort_by')), bridge)
))
```

That's fun.

There are a goodly number of possibly bridges that you can generate (139786), but it still only takes a few seconds to generate all of them and sort the results:

```bash
$ python3 run-all.py day-24

day-24  python3 maker-of-bridges.py input.txt --sort-by strength        6.030624866485596       Bridge(strength=1868, length=37, components=[(7, 0), (30, 7), (1, 30), (1, 1), (1, 50), (39, 50), (39, 39), (31, 39), (31, 13), (13, 50), (50, 50), (46, 50), (46, 26), (26, 41), (47, 41), (38, 47), (38, 34), (17, 34), (17, 43), (4, 43), (6, 4), (28, 6), (28, 2), (2, 23), (32, 23), (32, 28), (11, 28), (11, 21), (13, 21), (25, 13), (18, 25), (17, 18), (14, 17), (10, 14), (16, 10), (42, 16), (42, 42)])
day-24  python3 maker-of-bridges.py input.txt --sort-by length  6.264626979827881       Bridge(strength=1841, length=40, components=[(0, 9), (9, 28), (28, 2), (2, 23), (32, 23), (32, 28), (28, 6), (6, 4), (4, 43), (17, 43), (14, 17), (10, 14), (16, 10), (16, 7), (30, 7), (1, 30), (1, 1), (1, 50), (39, 50), (39, 39), (31, 39), (31, 13), (25, 13), (18, 25), (17, 18), (17, 34), (38, 34), (38, 47), (47, 41), (26, 41), (46, 26), (46, 50), (50, 50), (50, 19), (11, 19), (11, 21), (3, 21), (3, 24), (5, 24), (5, 5)])
```
