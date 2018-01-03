---
title: "AoC 2016 Day 13: Noisy Puzzle"
date: 2016-12-13
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [A Maze of Twisty Little Cubicles](http://adventofcode.com/2016/day/13)[^cca]

> **Part 1:** Generate a {{< wikipedia "procedurally generated" >}} maze using the following equation:

> - {{< inline-latex "x^2 + 3x + 2xy + y + y^2 + c" >}}

> `x` and `y` are the coordinates of a point and `c` is a constant.

> Count the number of bits for each point. Even is open spaces, odd is walls.

> What is the shortest route from `(0, 0)` to `(31, 39)`?

<!--more-->

The first half of this problem is generating the maze:

```python
parser.add_argument('--function', default = 'x*x + 3*x + 2*x*y + y + y*y + z', help = 'A function that determines walls, z is favorite below')
parser.add_argument('--favorite', required = True, help = 'The z parameter to --function')

def wall(x, y):
    '''Return if there is a wall at a given x,y'''

    z = int(args.favorite)

    if x < 0 or y < 0:
        return True
    else:
        value = eval(args.function)
        binary = bin(value)
        bits = binary.count('1')
        return bits % 2 == 1
```

Note: You should never use `eval` on untrusted input. :)

After you have that, it's another {{< wikipedia "breadth first search" >}} to find the shortest path:

```python
# A state is (x, y, steps)
def solve(start, target):
    '''Solve the given puzzle.'''

    q = queue.Queue()
    visited = set()

    q.put((start, []))

    while not q.empty():
        (x, y), steps = q.get()

        # If we've found the target, return how we got there
        if target and x == target[0] and y == target[1]:
            return steps

        visited.add((x, y))

        # Add any neighbors we haven't seen yet (don't run into walls)
        for xd, yd in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if (x + xd, y + yd) in visited:
                continue

            if wall(x + xd, y + yd):
                continue

            q.put(((x + xd, y + yd), steps + [(x, y)]))

    raise Exception('Cannot reach target')
```

You could instead use {{< wikipedia "A*" >}} for the pathfinding to save a bit on the runtime, but the search runs quickly enough.

As an added bonus, it's interesting to render these maps:

```python
def render(points, target = None):
    target_x, target_y = target if target else (10, 10)

    max_x = target_x
    max_y = target_y

    for (x, y) in points:
        max_x = max(max_x, x, target_x)
        max_y = max(max_y, y, target_y)

    max_x += 1
    max_y += 1

    for y in range(max_y + 1):
        for x in range(max_x + 1):
            if (x, y) in points:
                char = 'O'
            elif wall(x, y):
                char = 'X'
            else:
                char = '.'

            print(char, end = '')
        print()
```

I've used that to print the solution whenever I solved my own input:

```bash
$ python3 noisy-puzzle.py --favorite 1350 --target 31,39

=== Solution ===
XX.OOOXXX......X..X..X..XXXX.XXX..X..X.X
X.XXXXOXXXX..XXX.X.XX.X.X...X..X.X.XX.XX.
......OOXXXXXX.XXX..XXX..XX.X..XXX..XX.X.
X..XX.XOOXX..X.......XXX.X..XXX......X.XX
XXX.X...OOOO.XX.XX.X.....X....X.XX.X.XXX.
..XX.XXXXXXOX.X.XX...XXX.XX...XX.X..X..XX
.X.XX....XXOOXX.X.XXX..X.XXX.X.XX.X..X..X
.XX.X..X.XXXOX..X...X.XX...X..X.X..X.....
..XXXXXX..X.OX.XXXXXX.XXXXX.X..XXX..XX.XX
....X.....XXOX.XX..X...XX.X.XX.XXXX..X.XX
.XX.X.XX...XOOOOOO.X......X.....X.XXX...X
.X..X.XXX.XXXXXXXOXXXXXXXX.XX.X.XXX.XX...
.X..X..XX.X...XXXOXXOOOX.XX.X..X.....XX..
.XXX.X.XX.X.....XOOOOXOOX.XX.X.XXXX.X.X.X
.X.XXX...XXX.XX.X.XXX.XOXX.XXX...XX..XX.X
.X.....X..XX.X..XX..XX.O.X.....X..XX.X..X
.X..XXXXX....X...XXX.X.O.XX.XXXXX.X..X..X
XXX....X.XX.XXX.X..X.XXOX.XXX..X..XX.XXXX
X.XXX..XXXX..XX..X.X.XXOOXOOOOOX...X.X..X
XXX.X....X.X...X..XX..XXOOOXXXOXX.XX..X..
....XXX..XX.XX..X.XXX.X.XXXX.XOXX.XXX.X..
.XXXX.XX..XXXXXXX..X..X.....XXOOOOOX..XXX
.X.....XXX..X......X..XXX.X.X.XXX.OX.....
.X.XX.X..XX.X..XXXXXXXX.XXX.XXX.XXOXX..X.
.X.XX..X...XXXX....X.......X...X.XOXXXXX.
XX.X.X...X....X..X.X.XX..X.XXX..XXOXX...X
X..XX.XXXXXXXXXXXX.X.XXXXX....X.X.OOOOX.X
X.X.X.X..XX..X....XX..X....XX.X.X..XXOX..
X..XX.X....X.XX.X.X.X.X.XXX.X..XXXXXXOX.X
XX.X..XX.X..X.X.X.XX..XX..XX.X.....XOOXXX
...X.X.XX.X...X.XX.X...X.X.XXXXXX..XOX..X
X..X..X.X..XXX...X.XX.XX.XX..XX.X..XOOOO.
XX..X..XXX.X.X.X.XXXX.XX..X.....XX..XX.O.
XXX.XX.XXX..XX..X...X.....X..XXXXXX..XXOX
X.X.....X.X.X.X..XX.X.XX.XXXXX..X.XX.XXOX
XX.XXXX.XX..X..X.X..XX.X.XX..X..XXXX.XXO.
.XX....X.X.XXX...X...XX......XXX..XXOOOOX
..X..X.X.X.XXXX.XXX.X.XXXXX.X...XOOOOXX.X
.XXXXX.X....XXX..XX......XX..XXOOOXXX.X.X
..X...XXX.X..X.X...XX..X.XXX.X.XX.X.XX..X

92 steps/points
```

This amuses me. You can also render the search space as it's running, but that makes finding the solution far slower.

> **Part 2:** How many locations can you reach within 50 (inclusive) steps?

To do this, we can modify our `solve` function to take either a `target` or a `fill` count:

```python
def solve(start, target = None, fill = None):
    '''
    Solve the given puzzle.

    If target is a point, return the steps needed to get to that point
    If fill is a number, return all points that can be reached in that many steps
    '''

    q = queue.Queue()
    visited = set()

    q.put((start, []))

    while not q.empty():
        (x, y), steps = q.get()

        # If we're in target mode and found the target, return how we got there
        if target and x == target[0] and y == target[1]:
            return steps

        # If we're in fill mode and have gone too far, bail out
        if fill and len(steps) > fill:
            continue

        visited.add((x, y))

        # Add any neighbors we haven't seen yet (don't run into walls)
        for xd, yd in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if (x + xd, y + yd) in visited:
                continue

            if wall(x + xd, y + yd):
                continue

            q.put(((x + xd, y + yd), steps + [(x, y)]))

    if fill:
        return visited

    raise Exception('Cannot reach target')
```

Rendering works the same way:

```python
$ python3 noisy-puzzle.py --favorite 1350 --fill 50

=== Solution ===
XXOXXXXXX.XX.XXXXOOOX.XX....X.
OOOOOXX.X..X.XX.XOXOXXXXXX..X.
XXXOOOOXXX......XOOX..XOOXXXX.
XOXXXXOXXXX..XXX.XOXX.XOX...X.
OOOOOOOOXXXXXXOXXXOOXXXOOXX.X.
XOOXXOXOOXXOOXOOOOOOOXXXOX..XX
XXX.XOOOOOOOOXXOXXOXOOOOOX....
..XX.XXXXXXOX.XOXXOOOXXXOXX...
.X.XX....XXOOXXOX.XXX..XOXXX.X
.XX.X..X.XXXOXOOX...X.XXOOOX..
..XXXXXX..XOOXOXXXXXX.XXXXX.X.
....X.....XXOXOXXOOX...XX.X.XX
.XX.X.XX...XOOOOOOOX......X...
.X..X.XXX.XXXXXXXOXXXXXXXX.XX.
.X..X..XX.X...XXXOXXOOOX.XX.X.
.XXX.X.XX.X.....XOOOOXOOX.XX.X
.X.XXX...XXX.XX.XOXXX.XOXX.XXX
.X.....X..XX.X..XX..XXOOOX....
.X..XXXXX....X...XXX.XOOOXX.XX
XXX....X.XX.XXX.X..X.XXOX.XXX.
X.XXX..XXXX..XX..X.X.XXOOXOOO.
XXX.X....X.X...X..XX..XXOOOXXX
....XXX..XX.XX..X.XXX.X.XXXX.X

124 steps/points
```

[^cca]: {{< wikipedia "Colossal Cave Adventure" >}}
