---
title: "AoC 2017 Day 19: Networkout"
date: 2017-12-19
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2017
---
### Source: [A Series of Tubes](http://adventofcode.com/2017/day/19)

> **Part 1:** Take a network diagram of the following form:

> ```text
    |          
    |  +--+    
    A  |  C    
F---|--|-E---+
    |  |  |  D
    +B-+  +--+
```

> Starting at the single node at the top and following the lines, what order would the nodes be visited in?

<!--more-->

First, load the entire network:

```python
data = {}
points = {}
entry = None

def is_point(c):
    return re.match('[A-Z]', c)

for y, line in enumerate(lib.input()):
    for x, c in enumerate(line):
        if c.strip():
            data[x, y] = c

        if is_point(c):
            points[c] = (x, y)

        if y == 0 and c == '|':
            entry = (x, y)
```

Then, calculate the path:

```python
def path(pt):
    '''Yield all points along a given path.'''

    x, y = pt
    xd, yd = (0, 1)
    steps = 0

    while True:
        pt = x, y = x + xd, y + yd
        c = data.get(pt)

        if not c:
            break
        elif is_point(c):
            yield c
        elif c == '+':
            for new_xd, new_yd in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                # Back the way we came
                if new_xd == -xd and new_yd == -yd:
                    continue
                elif not data.get((x + new_xd, y + new_yd)):
                    continue
                else:
                    xd, yd = new_xd, new_yd
                    break

print(''.join(path(entry)))
```

That's fairly elegant. It's similar to a flood fill except there's always only one way to go. The two complications that come up are:

1. When crossing another line, you have to just ignore it and keep going. Only turn when you see a `+`.
2. When turning, make sure you don't go back the way you came.

> **Part 2:** How many steps did you take?

Only a slight tweak to count the path length along the way (using a global variable since I didn't want to change the return value since it was a generator):

```python
last_step_count = 0

def path(pt):
    '''Yield all points along a given path.'''

    global last_step_count
    last_step_count = 0
    ...

    while True:
        ...
        last_step_count += 1
        ...

print(last_step_count)
```

Quick.

```bash
$ python3 run-all.py day-19

day-19  python3 networkout.py input.txt 0.24499297142028809     DWNBGECOMY; 17228
```
