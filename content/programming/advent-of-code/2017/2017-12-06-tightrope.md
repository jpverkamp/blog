---
title: "AoC 2017 Day 6: Tightrope"
date: 2017-12-06
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Data Structures
series:
- Advent of Code 2017
---
### Source: [Memory Reallocation](http://adventofcode.com/2017/day/6)

> **Part 1:** Start with `n` stacks of different sizes. Take the largest block and distribute its items starting with `n+1` and looping around. How many iterations of this does it take before you see a state you've seen before?

<!--more-->

The core of this problem is getting the balancing function right:

```python
def balance(blocks):
    to_distribute = max(*blocks)
    index = blocks.index(to_distribute)

    for_each = to_distribute // len(blocks)
    left_over = to_distribute - (for_each * len(blocks))
    give_left_over_to = {i % len(blocks) for i in range(index + 1, index + 1 + left_over)}

    return tuple(
        (
            (amount if i != index else 0)
            + for_each
            + (1 if i in give_left_over_to else 0)
        )
        for i, amount in enumerate(blocks)
    )
```

The blocks are defined as a {{< doc python tuple >}} since that allows it to be used as an element in a {{< doc python set >}} (lists don't work since they are [[wiki:mutable]]()).

To actually distribute the blocks, we will start by dividing the amount and keeping the remainder. The quotient `for_each` goes to all of the blocks and the remainder `left_over` is the odd bits that will only go to some of the blocks. `give_left_over_to` is me figuring out which indexes are going to get the remainder. Finally, we create a new tuple by adding the current amount (except for the block we're redistributing) plus `for_each` plus 1 for those `left_over`.

Then we'll loop over those until we see a duplicate:

```python
blocks = tuple(
    int(node)
    for line in lib.input()
    for node in line.split()
)

seen = set()
for cycle in itertools.count():
    if blocks in seen:
        break
    else:
        seen.add(blocks)

    blocks = balance(blocks)

print(cycle)
```

> **Part 2:** How many iterations are there in the loop?

Interesting. To do this, what we want to do is store the index we see each arrangement of blocks at, rather than just that we saw them. Then the difference between the current iteration and that first one is the length of the cycle:

```python
seen = {}
for cycle in itertools.count():
    if blocks in seen:
        break
    else:
        seen[blocks] = cycle

    blocks = balance(blocks)

print(cycle, cycle - seen[blocks])
```

This will run both parts in a single command:

```bash
$ python3 run-all.py day-06

day-06  python3 tightrope.py input.txt  0.10088086128234863     3156 1610
```
