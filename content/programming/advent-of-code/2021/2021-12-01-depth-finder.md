---
title: "AoC 2021 Day 1: Depth Finder"
date: 2021-12-01 00:00:03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Depth Finder](https://adventofcode.com/2021/day/1/answer)

#### **Part 1:** Given a list of numbers, count how many times sequential numbers increase.

<!--more-->

I'm going to be using the excellent [typer](https://typer.tiangolo.com/) library this time to make CLIs. Assume that I've always made `app = typer.Typer()` and have a `app()` in the main function. With that, all we have to do is write typed functions decorated with `@app.command()` (which I'll also leave out). 

```python
def part1(data: typer.FileText):
    count = 0
    last_depth = None

    for line in data:
        current_depth = int(line)

        if last_depth and current_depth > last_depth:
            count += 1

        last_depth = current_depth

    print(count)
```

That's the straight forward way to do the problem. Keep track of the previous value, if we have an increase, bump `count`, and then print it at the end:

```bash
$ python3 depth-finder.py part1 input.txt
1393
```

#### **Part 2:** Do the same with a 3-width sliding window.

A bit more complicated, so of course I'm going to completely do this one in a different more functional style:

```python
def part2(data: typer.FileText, window_size: typing.Optional[int] = typer.Argument(1)):
    # Convert all depths to ints
    depths = list(map(int, data))

    # Calculate each window (depth[...]) and the sum of depths for each window
    slices = [
        sum(depths[start: start + window_size])
        for start in range(len(depths) - window_size + 1)
    ]

    # Count if we have an increase (b > a) for each pair of depths
    print(sum(
        1 if b > a else 0
        for a, b
        in zip(slices, slices[1:])
    ))
```

Comments this time because it's a bit more interesting. But essentially we have (as commented) three steps:

1. Convert from strings to ints (can typer do this for me?)
2. Calculate the windows using slices of lists (there should be something in itertools that does this for me, [pairwise](https://docs.python.org/3/library/itertools.html#itertools.pairwise) works for n=2 and [more-itertools](https://more-itertools.readthedocs.io/en/stable/api.html) has a `sliding_window` function built in that does this)
3. For each pair of windows (using the `zip(ls, ls[1:])` pattern), count if we increased using a generator + `sum`

It's perhaps not the easiest to read code for everyone, but I think it's elegant enough.

```bash
$ python3 depth-finder.py part2 input.txt 3
1359
```

If you want this written in the style of part1 instead:

```python
def part2_simple(data: typer.FileText, window_size: typing.Optional[int] = typer.Argument(1)):
    count = 0
    last_depth = None

    # typer.FileText does not work with len or slices, so convert to a list
    data = list(data)

    for start in range(len(data) - window_size):
        current_depth = sum(map(int, data[start: start + window_size]))

        if not last_depth or current_depth > last_depth:
            count += 1

        last_depth = current_depth

    print(count)
```

With this tiny of input data... the timing doesn't change at all:

```bash
$ python3 depth-finder.py part2-simple input.txt 3
1359
```

Using the [test harness](https://github.com/jpverkamp/advent-of-code/blob/master/2021/all.py) I mentioned in the [summary post]({{< ref "2021-12-01-advent-of-code-2021" >}}):

```bash
--- Day 1: Sonar Sweep ---

$ python3 depth-finder.py part1 input.txt
1393
# time 46772375ns / 0.05s

$ python3 depth-finder.py part2 input.txt 3
1359
# time 34292250ns / 0.03s

$ python3 depth-finder.py part2-simple input.txt 3
1359
# time 34505708ns / 0.03s
```

It is interesting that either windowed solution is slightly faster than the non-windowed solution though. A few less iterations? Cached file contents? Wouldn't think it would matter that much, but so it goes. 