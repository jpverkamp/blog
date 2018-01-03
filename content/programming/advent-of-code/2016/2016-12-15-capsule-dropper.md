---
title: "AoC 2016 Day 15: Capsule Dropper"
date: 2016-12-15
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Timing is Everything](http://adventofcode.com/2016/day/15)

> **Part 1:** Given a series of openings one second apart, each with `n` positions that advance one position per second, what is the first time you can start the simulation so that you pass each in position `0`.

<!--more-->

Not much to say about this one. Load the disks and then check each disk. The most interesting part is using {{< wikipedia "modular arithmetic" >}} so that you don't have to actually determine the current position--just check if it's 0.

```python
discs = []

for line in fileinput.input(args.files):
    if not line.strip() or line.startswith('#'):
        continue

    m = re.match(r'Disc #(\d+) has (\d+) positions; at time=0, it is at position (\d+).', line)
    index, count, current = m.groups()
    discs.append((int(index), int(count), int(current)))

def solve():
    for button_press in naturals():
        success = True

        for (index, count, current) in discs:
            if (button_press + index + current) % count != 0:
                success = False
                break

        if success:
            return button_press

print('Press the button at t = {}'.format(solve()))
```

> **Part 2:** Add a new opening at the end with `11` positions.

This doesn't actually change the problem. It just makes it slower. But it still finishes well within a minute, so not much point in optimizing it. 
