---
title: "AoC 2021 Day 7: Brachyura Aligner"
date: 2021-12-07 00:00:10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [The Treachery of Whales](https://adventofcode.com/2021/day/7)

#### **Part 1:** Given a list of numbers, find the minimum integer `I` such the sum difference of each number and I is minimized. 

There is probably a fancy number theory way of doing it to solve directly for `I`, but it's a really quick problem to brute force:

```python
def part1(file: typer.FileText):

    positions = [
        int(value)
        for line in file
        for value in line.split(',')
    ]

    fuel, target = min(
        (
            sum(abs(position - target) for position in positions),
            target
        )
        for target in range(min(positions), max(positions)+1)
    )

    print(f'{target=}, {fuel=}')
```

Load in the numbers, calculate every possible `target` from minimum to maximum and the sum distance for that value of `I`, then return just the minimum such value. 

```bash
$ python3 brachyura-aligner.py part1 input.txt
target=323, fuel=336040
```

Quick.

<!--more-->

#### **Part 2:** Instead of using the distance function `|I-n|`, instead use `d(1)=1, d(2)=3, d(3)=6`, etc (the {{< wikipedia "triangular numbers" >}}). 

It actually originally said:

> Instead, each change of 1 step in horizontal position costs 1 more unit of fuel than the last: the first step costs 1, the second step costs 2, the third step costs 3, and so on.

That ends up turning into `1, 3, 6, 10, ...` which I recognized as the Triangular numbers. And it turns out there isa direct formula for calculating the nth Triangular number:

{{< latex >}}
t(n) = \frac{n(n-1)}{2}
{{< /latex >}}

```python
def part2(file: typer.FileText):

    def t(n):
        return n * (n + 1) // 2

    positions = [
        int(value)
        for line in file
        for value in line.split(',')
    ]

    fuel, target = min(
        (
            sum(t(abs(position - target)) for position in positions),
            target
        )
        for target in range(min(positions), max(positions)+1)
    )

    print(f'{target=}, {fuel=}')
```

And off we go:

```bash
$ python3 brachyura-aligner.py part2 input.txt
target=463, fuel=94813675
```

It is interesting how that changes the answer, but I expect that's because distance scale much more quickly, so extremes matter more than in part 1.

#### Optimization

One optimization that you can notice is that either of these functions still results in a function with a single local minimum (the solution). Let's show that:

```python
last_score = 0

for target in range(min(positions), max(positions)+1):
    score = sum(t(abs(position - target)) for position in positions)

    if last_score:
        print('=' if score == last_score else ('^' if score > last_score else 'v'), end='')

    last_score = score
```

For each score, we're going to print `^` if the score is currently rising and `v` if it's falling. 

```text
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

Swaps right at 463 (as expected). So one optimization would be to start at the low end and wait until it swaps. Another would be to do a binary search, looking for that inversion point. In either case though... 

```bash
--- Day 7: The Treachery of Whales ---

$ python3 brachyura-aligner.py part1 input.txt
target=323, fuel=336040
# time 140666042ns / 0.14s

$ python3 brachyura-aligner.py part2 input.txt
target=463, fuel=94813675
# time 284611417ns / 0.28s
```

It doesn't seem necessary. It's the slowest problem so far, but by no means slow. After all:

> The real problem is that programmers have spent far too much time worrying about efficiency in the wrong places and at the wrong times; premature optimization is the root of all evil (or at least most of it) in programming.
> 
> -- Donald Knuth, *The Art of Computer Programming*

:smile: