---
title: "AoC 2016 Day 6: Signal Unjammer"
date: 2016-12-06
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Signals and Noise](http://adventofcode.com/2016/day/6)

> **Part 1:** Given a list of strings, find the most common character in each position.

<!--more-->

One reason I love Python's {{< doc python defaultdict >}} (although it's never strictly necessary). I can make a nested map of `position -> character -> count` that automatically defaults to `0` without having to worry at all if I'm seeing the index/character for the first time or not.

```python
from collections import defaultdict as ddict

counters = ddict(lambda : ddict(lambda : 0))

with open(args.input, 'r') as fin:
    for line in fin:
        for index, character in enumerate(line.strip()):
            counters[index][character] += 1

print(''.join(
    max((count, character) for character, count in counters[index].items())[1]
    for index in sorted(counters)
))
```

> **Part 2:** Find the least common character for each position (that occurs at least once).

Interesting. It's the same code, except using `min` instead of `max`. In fact:

```python
for comparator in (max, min):
    print(comparator.__name__, ''.join(
        comparator((count, character) for character, count in counters[index].items())[1]
        for index in sorted(counters)
    ))
```

Magic.
