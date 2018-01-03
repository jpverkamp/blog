---
title: "AoC 2016 Day 22: Data Mover"
date: 2016-12-22
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2016
---
### Source: [Grid Computing](http://adventofcode.com/2016/day/22)

> **Part 1:** You are given a grid of nodes and the output of the {{< wikipedia page="DF (unix)" text="df command" >}} telling you how much space is on each. How many pairs of nodes are there where the data from some node `A` would fit entirely on `B`?

<!--more-->

First, load the data:

```python
sizes = {}
usage = {}

for line in fileinput.input(args.files):
    if not line.startswith('/dev/grid/'):
        continue

    name, size, used, available, percent = line.strip().split()
    _, xs, ys = name.split('/')[-1].split('-')
    x = int(xs[1:])
    y = int(ys[1:])

    sizes[x, y] = int(size[:-1])
    usage[x, y] = int(used[:-1])
```

Then, just directly calculate if we can move the data:

```python
viable_pairs = set()

for a in sizes:
    if usage[a] == 0:
        continue

    for b in sizes:
        if a == b:
            continue

        if usage[a] + usage[b] <= sizes[b]:
            viable_pairs.add((a, b))

print('{} viable pairs'.format(len(viable_pairs)))
```

> **Part 2:** Assume you can only move data between adjacent nodes and if you do so, you must move all data. How many transfers would it take to move data from the node with `y=0` and the highest `x` value (the top right) to `x=0, y=0` (the top left)?

This is actually quite a bit harder than you might at first guess, especially if you don't read the huge hint they give you when given a smaller example.

If you don't use the hint, you might want to try a {{< wikipedia "brute force" >}} {{< wikipedia "breadth first search" >}}:

```python
initial_state = (copy.deepcopy(usage), (max_x, 0), 0)

q = queue.Queue()
q.put(initial_state)
seen = set()

while True:
    if q.empty():
        raise Exception('Ran out of possibilities to test')

    current_usage, goal, steps = q.get()

    current_hash = hash_state(current_usage, goal)
    if current_hash in seen:
        continue
    else:
        seen.add(current_hash)

    if (0, 0) == goal:
        print('Found a solution in {} steps'.format(steps))
        break

    # Try moving everything everywhere
    # TODO: Improve this :)
    nodes_added = 0

    for x in range(max_x + 1):
        for y in range(max_y + 1):
            for xd, yd in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if not (0 <= x + xd <= max_x and 0 <= y + yd <= max_y):
                    continue

                # Make sure we can move the given data
                total_size = current_usage[x, y] + current_usage[x + xd, y + yd]
                if total_size <= sizes[x + xd, y + yd]:
                    new_usage = copy.deepcopy(current_usage)
                    new_usage[x, y] = 0
                    new_usage[x + xd, y + yd] = total_size

                    if (x, y) == goal:
                        q.put((new_usage, (x + xd, y + yd), steps + 1))
                    else:
                        q.put((new_usage, goal, steps + 1))

                    nodes_added += 1
```

The problem with that is that the solution space is kind of huge... I let it run for a while, but after well longer than the minute I expect problems to be able to solved in (Project Euler rules), I decided that we needed something a bit more clever.

*If you're trying to solve this problem by yourself and are for some reason reading this post, stop reading now.*

The hint: there are three classes of nodes:

- A single node that is nearly empty, think of this as the node we're actually 'moving' around
- Several nodes that are nearly full, but have lower capacity similar to the empty node, these are empty space we can move in
- Several more nodes that are nearly full but have much more data (> 5x as much) as the empty node, so that we couldn't possibly copy data into the empty node

We can render this using this function:

```python
def print_usage_icons(usage, goal):
    '''Print based on the hint in the puzzle.'''

    for y in range(max_y + 1):
        for x in range(max_x + 1):
            if (x, y) == goal:
                output = 'G'
            elif usage[x, y] == 0:
                output = '@'
            elif sizes[x, y] > 500:
                output = '#'
            else:
                output = '.'

            print(output, end = '')
        print()
```

Visually, this gives us:

```text
.....................................G
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
.#####################################
......................................
......................................
......................................
......................................
......................................
......................................
......................................
......................................
.................@....................
......................................
......................................
......................................
```

That makes it quite a bit more obvious that there is a central 'wall' of large nodes that we just have to go around. We can use this information: to get the goal data to the top left, we have to first move the empty spot to directly beside the goal data. After we've done that, we 'walk' it across by moving the empty data down, right, right, up, left in a continuous loop. In code, this lets us guess:

```python
# Find the empty node
for x in range(max_x + 1):
    for y in range(max_y + 1):
        if usage[x, y] == 0:
            (empty_x, empty_y) = empty = (x, y)

# Find walls (nodes with more than 500T data)
walls = {
    (x, y)
    for x in range(max_x + 1)
    for y in range(max_y + 1)
    if sizes[x, y] > 500
}

# Use dynamic programming to find the minimum distance between two points
distance_from_empty = {}
to_calculate = queue.Queue()

to_calculate.put((empty, 0))
while not to_calculate.empty():
    point, distance = to_calculate.get()
    if point in distance_from_empty:
        continue

    distance_from_empty[point] = distance

    (x, y) = point
    for xd, yd in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (x + xd, y + yd)
        if 0 <= x + xd <= max_x and 0 <= y + yd <= max_y and neighbor not in walls:
            to_calculate.put((neighbor, distance + 1))

# Move to immediately beside the goal
distance_to_goal = distance_from_empty[(max_x - 1, 0)]

# Now it takes 5 to move the goal one left and reset (except the last time)
distance_to_zero = 5 * (max_x - 1) + 1

print('Best guess = {} ({} to goal + {} to zero)'.format(
    distance_to_goal + distance_to_zero,
    distance_to_goal,
    distance_to_zero,
))
```

Using this solution gives us an answer in less than a second which turns out to be completely correct. Running the full solution for more than a day gives the same answer.

Sometimes, a heuristic solution is good enough.
