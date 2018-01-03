---
title: "AoC 2016 Day 1: Taxicab Simulator"
date: 2016-12-01 00:00:02
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [No Time for a Taxicab](http://adventofcode.com/2016/day/1)

> **Part 1:** Starting at `0,0` and given a string of `L#` / `R#` to turn left / right and move `#` squares, where do you end up?

<!--more-->

```python
location = 0+0j
facing = 1+0j

rotations = {'R': 0+1j, 'L': 0-1j}

with open(args.input_file, 'r') as fin:
    for command in fin.read().split(', '):
        facing *= rotations[command[0]]

        for step in range(int(command[1:])):
            location += facing

def format_location(pt):
    return '({}, {}), {} blocks from the origin'.format(
        abs(int(pt.real)),
        abs(int(pt.imag)),
        abs(int(pt.real)) + abs(int(pt.imag)),
    )

print('final location:', format_location(location))
```

We're going to use a trick I've used before and using complex numbers for points. This lets us add them together easily and lets us use complex multiplication for the rotations (multiplying by `0+1i` is the same as rotating clockwise).

> **Part 2:** How many blocks away is the first location you visit twice?

For this, we just have to track the points we've visited (in a {{< doc python set >}}) and write down the first duplicate we find.

```python
visited = {0+0j}
first_duplicate = None

with open(args.input_file, 'r') as fin:
    for command in fin.read().split(', '):
        facing *= rotations[command[0]]

        for step in range(int(command[1:])):
            location += facing

            if location in visited:
                if first_duplicate == None:
                    first_duplicate = location
            else:
                visited.add(location)

...

print('first duplicate:', format_location(first_duplicate))
```

Easy enough. Onwards!
