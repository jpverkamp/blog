---
title: "AoC 2017 Day 15: Two Generators"
date: 2017-12-15
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Generators
series:
- Advent of Code 2017
---
### Source: [Dueling Generators](http://adventofcode.com/2017/day/15)

> **Part 1:** Create a pair of generators `A` and `B` where:

> - {{< inline-latex "A_n = 16807 A_{n-1} \mod 2147483647" >}}
> - {{< inline-latex "B_n = 48271 B_{n-1} \mod 2147483647" >}}

> How many of the first 40 million values have matching values for the low 16 bits of each generator?

<!--more-->

Let's make some literal {{< doc python generators >}}:

```python
lib.add_argument('--seeds', nargs = 2, type = int, required = True)
lib.add_argument('--factors', nargs = 2, type = int, default = (16807, 48271))
lib.add_argument('--modulus', type = int, default = 2147483647)

def make_generator(value, factor, modulus):
    while True:
        value = value * factor % modulus
        yield value

generator_a, generator_b = [
    make_generator(lib.param('seeds')[i], lib.param('factors')[i], lib.param('modulus'))
    for i in (0, 1)
]
```

This actually puts most of the work on {{< doc python argparse >}} and putting in the values on the command line.

Take the generators and use binary and `&` to mask out the low bits and we have something:

```python
lib.add_argument('--mask', type = int, default = 0xffff)
lib.add_argument('--pairs', type = int, default = 40000000)

matching_masks = 0

for i, a, b in zip(range(lib.param('pairs')), generator_a, generator_b):
    masked_a = a & lib.param('mask')
    masked_b = b & lib.param('mask')

    if masked_a == masked_b:
        matching_masks += 1
        lib.log(f'index {i} ({a} and {b}) match, {matching_masks} so far')

print(f'{matching_masks} match')
```

> **Part 2:** Only consider values from `A` that are multiples of `4` and values from `B` that are multiples of `8`. Consider only the first 5 million pairs.

Add another parameter and pass it through to `make_generator`:

```python
lib.add_argument('--filters', nargs = 2, type = int, default = (1, 1))

generator_a, generator_b = [
    make_generator(lib.param('seeds')[i], lib.param('factors')[i], lib.param('modulus'), lib.param('filters')[i])
    for i in (0, 1)
]

def make_generator(value, factor, modulus, multiple_filter):
    while True:
        value = value * factor % modulus

        if value % multiple_filter == 0:
            yield value
```

Even running through 1/8 as many values still takes rather a while. Amusingly though, since I'm actually running the part 1 test case with the default `--filters 1 1`, it's the slower one in the `run-all.py` output:

```bash
$ python3 run-all.py day-15

day-15  python3 two-generators.py --seeds 618 814       91.80951809883118       577 match
day-15  python3 two-generators.py --seeds 618 814 --filters 4 8 --pairs 5000000 27.60622811317444       316 match
```

If you take that code away though, it runs much more quickly (under a minute).

Neat.
