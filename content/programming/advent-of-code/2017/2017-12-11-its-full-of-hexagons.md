---
title: "AoC 2017 Day 11: It's Full Of Hexagons"
date: 2017-12-11
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2017
---
### Source: [Hex Ed](http://adventofcode.com/2017/day/11)[^punny]

> **Part 1:** Work on a hex grid:
>
> ```
>   \ n  /
> nw +--+ ne
>   /    \
> -+      +-
>   \    /
> sw +--+ se
>   / s  \
> ```
> Given a series of steps (`n`, `se`, `ne`) etc, how many steps away from the origin do you end up?

<!--more-->

This problem mostly comes down to representation. [This post from Red Blob games](https://www.redblobgames.com/grids/hexagons/) has the best write up of how to use hex coordinate systems I've ever seen. Since it handles distances better, I'm going to use a cube coordinate system, where each hex actually has an `x`, `y`, and `z` coordinate. Now that is decided, we can write up a map to translate directions into offsets, a way to add points together, and a distance function:

```python
neighbors = {
    'n' : (0, 1, -1),
    'ne': (1, 0, -1),
    'se': (1, -1, 0),
    's' : (0, -1, 1),
    'sw': (-1, 0, 1),
    'nw': (-1, 1, 0),
}

def add(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return (x1 + x2, y1 + y2, z1 + z2)

def move(p, d):
    return add(p, neighbors[d.strip()])

def distance(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))
```

That makes code for the actual question nice and clean:

```python
origin = (0, 0, 0)

for line in lib.input():
    point = origin

    for direction in line.split(','):
        point = move(point, direction)

    distance_to_origin = distance(origin, point)
    print(f'ended at {point} ({distance_to_origin} from origin)')
```

> **Part 2:** What is the furthest point from the origin visited?

Similar to [day 8]({{< ref "2017-12-08-conditiputer.md" >}}), we just need to track the maximum value seen thus far as we go:

```python
for line in lib.input():
    point = origin
    furthest_distance = 0
    furthest_point = None

    for direction in line.split(','):
        point = move(point, direction)

        distance_to_origin = distance(origin, point)
        if distance_to_origin > furthest_distance:
            furthest_distance = distance_to_origin
            furthest_point = point

    print(f'ended at {point} ({distance_to_origin} from origin); furthest was {furthest_point} ({furthest_distance} from origin)')
```

That's a pretty interesting problem as well.

```bash
$ python3 run-all.py day-11

day-11  python3 its-full-of-hexagons.py input.txt       0.0798640251159668      ended at (650, -313, -337) (650 from origin); furthest was (1465, -1070, -395) (1465 from origin)
```

[^punny]: Not sure who's being punnier here. :smile:
