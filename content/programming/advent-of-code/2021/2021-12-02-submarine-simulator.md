---
title: "AoC 2021 Day 2: Submarine Simulator"
date: 2021-12-02
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Dive!](https://adventofcode.com/2021/day/2)

#### **Part 1:** Simulate a submarine with 3 commands: `forward N`, `down N`, and `up N` that move forward, increase depth, and decrease depth in that order. Calculate the product of the final position and depth.

<!--more-->

Let's just hit this one directly:

```python
def part1(commands: typer.FileText):
    position, depth = 0, 0

    for command in commands:
        key, value = command.split()
        value = int(value)

        if key == 'forward':
            position += value
        elif key == 'down':
            depth += value
        elif key == 'up':
            depth -= value

    print(f'{position=}, {depth=}, {position*depth=}')
```

Keep track of the current `position` and `depth` and then for every command, update them as needed. We can totally make this submarine fly out of the water, but that's not mentioned in the problem!

The final output is the product of the final position and depth, so print all that out:

```bash
$ python3 submarine-simulator.py part1 input.txt
position=2007, depth=747, position*depth=1499229
```

Cool. 

#### **Part 2:** Change `down` and `up` so that they angle the submarine instead. Now `foward N` moves both forward and decreases/increases depth by the current angle * the speed. Calculate `position * depth` with this new setup.

This is mostly understanding the prompt:

```python
def part2(commands: typer.FileText):
    position, depth, aim = 0, 0, 0

    for command in commands:
        key, value = command.split()
        value = int(value)

        if key == 'forward':
            position += value
            depth += aim * value
        elif key == 'down':
            aim += value
        elif key == 'up':
            aim -= value

    print(f'{position=}, {depth=}, {position*depth=}')
```

We do go *quite* a bit deeper though:

```bash
$ python3 submarine-simulator.py part2 input.txt
position=2007, depth=668080, position*depth=1340836560
```

Onward!