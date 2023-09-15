---
title: "AoC 2016 Day 16: Dragon Data"
date: 2016-12-16
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Procedural Content
series:
- Advent of Code 2016
---
### Source: [Dragon Checksum](http://adventofcode.com/2016/day/16)

> **Part 1:** Generate noise using a modified [[wiki:dragon curve]]():

> - Start with data `a`
> - Create a copy of the data `b`, reverse and invert it (0 <-> 1)
> - Create the string `a0b`

> Repeat until you have enough data, truncate at the end if needed.

> From this string calculate a checksum as follows:

> - [[wiki:xor]]() each pair of bits, concatenate the results
> - If the resulting string has an even length, repeat; if it's odd, stop

> Calculate the checksum of a given initial state expanded to `272` bits.

<!--more-->

To solve this, we turn the two halves of the problem directly into functions. Since strings are [[wiki:immutable]]() in python, uses lists of `0` and `1`. First, expand the data to fill the given length:

```python
def dragon(ls, length):
    while len(ls) < length:
        ls = ls + [0] + list(reversed([0 if el else 1 for el in ls]))

    return ls[:length]
```

Then calculate the checksum:

```python
def checksum(ls):
    logging.info('Checksum of: {}'.format(ls))

    if len(ls) % 2 == 0:
        return checksum([(1 if a == b else 0) for (a, b) in zip(ls[0::2], ls[1::2])])
    else:
        return ls
```

The trick here is using the third argument to a slice to skip every other value--`ls[0::2]` is every other value starting with 0, `ls[1::2]` is the same but starting at the second element.

Put them together:

```python
ls = list(map(int, args.seed))
sum = checksum(dragon(ls, args.length))

print(''.join(map(str, sum)))
```

Fin.

> **Part 2:** Do the same thing except expand to `35651584` bits.

The same code works for this solution. Even though it's quite a bit slower, it still runs without crashing and quickly enough, so no need to optimize.

If you wanted to optimize this, the likely solution would be to realize that you can split the problem in half and solve each half fairly easily. You only have to deal with some weirdness if the length at any point expanding is odd.
