---
title: "AoC 2021 Day 15: Low Ceiling Simulator"
date: 2021-12-15
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Algorithms
- A*
- Optimization
---
### Source: [Chiton](https://adventofcode.com/2021/day/15)

#### **Part 1:** Given a grid of weights, find the minimum path from top left to top right. Return the total weight along that path. 

<!--more-->

A fairly standard thing to have to do, ripe for the {{< wikipedia "A* search algorithm" >}}. Which eventually I'll get to, but I'll admit, it wasn't the first algorithm I tried. :smile:

Let's do this. First, let's assume that we already have a `load` function that returns a map of `(x, y) -> cost` as we've done a number of times before. No matter what algorithm we use, the wrapping code is going to be the same:

```python
def part1(file: typer.FileText):

    map = load(file)
    best_path = explore(map)
    best_score = sum(map[x, y] for (x, y) in best_path[1:])

    logging.info(f'{best_path=}')
    print(f'{best_score=}')
```

Now, all we have to do is write an explore function. The first algorithm I tried was to write a cached recursive function (like last time). Essentially: 

{{< latex >}}
bestPath(x, y) = cost(x,y) + minimum \left\{\begin{matrix}
bestPath(x+1, y) \\ 
bestPath(x-1, y) \\ 
bestPath(x, y+1) \\ 
bestPath(x, y-1)
\end{matrix}\right.
{{< /latex >}}

You have to make sure that you don't recur infinitely (so you have to pass around the points you've visited so you don't form loops), but other than that, it should work... Except Python isn't really designed for that. Oh the number of 'maximum recursion depth reached' errors I got. Anyways. 

Next solution: 

* Start with a map of 'best known paths' from each point to the goal (store the path + the cost)
* Until the map has stabilized (doesn't change for an entire loop), loop across every point (x, y)
    * For each point, check each four neighbors for their minimum (path, cost)
    * If their (path, cost) + your cost is less than your current cost (or yours hasn't been set), store it

That means that you'll eventually fill in the entire graph. It's not super efficient, since you're going to be running it from top left to bottom right, where the grid fills from bottom right to top left... but it does work. 

```bash
$ python3 low-ceiling-simulator.py part1 input.txt
best_score=687
# time 2041809750ns / 2.04s
```

That's... fairly slow already for such a small graph... but it works for part one. How does the code work?

```python
def explore(map: Mapping[Point, int]) -> List[Point]:
    '''
    Version 1: Brute force, update all paths and iterate until stable. 
    '''

    width = max(x + 1 for (x, _) in map)
    height = max(y + 1 for (_, y) in map)

    bottom_right = (width - 1, height - 1)

    best_paths = {
        bottom_right: (1, [bottom_right])
    }

    # Pass until the best path map stops changing
    best_paths_changed = True
    generation = 0

    while best_paths_changed:
        best_paths_changed = False
        generation += 1
        logging.info(f'{generation=}, {len(best_paths)}/{len(map)} paths populated')

        for x in range(width):
            for y in range(height):
                neighbor_scores = [
                    best_paths[x + xd, y + yd]
                    for xd, yd in ORTHAGONAL
                    if (x + xd, y + yd) in best_paths
                ]

                if not neighbor_scores:
                    continue

                # Find the best neighbor
                best_score, best_path = min(neighbor_scores)

                new_score = map[x, y] + best_score
                new_path = [(x, y)] + best_path

                # If we haven't found a path for this point or we found a better one, update
                if not (x, y) in best_paths or new_score < best_paths[x, y][0]:
                    best_paths_changed = True
                    best_paths[x, y] = (new_score, new_path)

    return best_paths[0, 0][1]
```

More or less exactly what I described in the psuedo-code, just much longer. 

Okay, let's see what part 2 has in store for us!

#### **Part 2:** Extend the map 5x in each direction. Each time you copy the map right/down, increase all values by 1, wrapping 10 back to 1. Calculate the new shortest path.

Yeah. That's what I was worried about. It was already taking 2 seconds for a 100x100 grid and now we have to do 500x500. And that's not just 25 times as many paths... Even if you assume you can only go right or down (we'll come back to that), that's still a lot of paths...

{{< latex >}}
paths(N) = \binom{2(N-1)}{N-1}
{{< /latex >}}

{{< inline-latex "paths(10, 10) = 48620" >}}, {{< inline-latex "paths(100, 100) = 2.27x10^{58}" >}}, {{< inline-latex "paths(500) = 6.76x10^{298}" >}}

Yeah. That grows fast. The algorithm that I wrote in part 1 certainly doesn't check all of those, but it's still far slower than I'd like:

```bash
$ python3 low-ceiling-simulator.py part2 input.txt
best_score=2957
# time 425408701709ns / 425.41s
```

Okay, before we go anywhere, let's build that new map. Not that bad, but a bit interesting to properly handle the increasing/changing values:

```python
def part2(file: typer.FileText):

    original_map = load(file)
    map: MutableMapping[Point, int] = dict(original_map)

    width = max(x + 1 for (x, _) in map)
    height = max(y + 1 for (_, y) in map)

    for bigx in range(5):
        for bigy in range(5):
            offset = bigy + bigy

            for x in range(width):
                for y in range(height):
                    newx = x + bigx * width
                    newy = y + bigy * height

                    map[newx, newy] = (map[x, y] + bigx + bigy)
                    if map[newx, newy] > 9:
                        map[newx, newy] -= 9

    best_path = explore(map)
    best_score = sum(map[x, y] for (x, y) in best_path[1:])

    logging.info(f'{best_path=}')
    print(f'{best_score=}')
```

Cool. 

Now let's explore a few more choices. First, let's assume that you can only go down or right. That makes the algorithm much simpler, since you can essentially start in the bottom right and fill in each square that has a value down and right of itself. Something like this:

```python
def explore_2(map: Mapping[Point, int]) -> List[Point]:
    '''
    Version 2: Scan from the bottom right.

    NOTE: This version cannot handle paths that move up or left.
    '''

    width = max(x + 1 for (x, _) in map)
    height = max(y + 1 for (_, y) in map)

    bottom_right = (width - 1, height - 1)

    best_paths = {
        bottom_right: (1, [bottom_right])
    }

    # Start with the two points adjacent to bottom right
    to_scan = [
        (width - 2, height - 1),
        (width - 1, height - 2),
    ]

    while to_scan:
        (x, y) = to_scan[0]
        to_scan = to_scan[1:]

        # If it's out of bounds, skip
        if (x, y) not in map:
            continue

        # If it's already been scanned, skip
        if (x, y) in best_paths:
            continue

        logging.info(f'Scanning ({x}, {y}), {len(to_scan)}/{len(map)} remaining')

        # Find the best path to get to this point
        neighbors = [
            best_paths[x + xd, y + yd]
            for xd, yd in ORTHAGONAL
            if (x + xd, y + yd) in best_paths
        ]

        best_score, best_path = min(neighbors)

        best_paths[x, y] = (
            map[x, y] + best_score,
            [(x, y)] + best_path
        )

        # Add adjacent points to scan next
        # We'll handle duplicates and out of bounds at the top of the loop
        for xd, yd in ORTHAGONAL:
            to_scan.append((x + xd, y + yd))

    return best_paths[0, 0][1]
```

It's using a queue to keep track of where we're going, so essentially scanning in a circle from the bottom right (that makes the code a bit longer). But, it only takes one past and doesn't have to settle. But most importantly, is it faster? (And I guess... does it work?)

```bash
$ python3 low-ceiling-simulator.py --version 2 part2 input.txt
best_score=2962
# time 6651538833ns / 6.65s
```

Yes! ... and no. 

It does return much faster, only taking a few seconds. But it doesn't actually work. It seems that somewhere in my actual input data, there is a case where it's cheaper to go back up/left and loop a bit than to always go directly down/right. Fascinating. But it also means that, while fast, this algorithm is a no go. 

So let's go back to part 1 and mix in a bit of part 2 to try to make it a little smarter. Continue with the same 'iterate until stable' algorithm, but instead of starting in the top left, start in the bottom right. That should mean we can fill in initial values for the entire graph in one pass, then only start cleaning up after that. It will do roughly the same amount of work, but should converge a lot faster. Something like this:

```python
def explore_3(map: Mapping[Point, int]) -> List[Point]:
    '''
    Version 3: Iterate until stable again, but this time from the bottom right.
    '''

    width = max(x + 1 for (x, _) in map)
    height = max(y + 1 for (_, y) in map)

    bottom_right = (width - 1, height - 1)

    best_paths = {
        bottom_right: (1, [bottom_right])
    }

    changed_paths = 1
    while changed_paths:
        changed_paths = 0

        for x in range(width - 1, -1, -1):
            for y in range(height - 1, -1, -1):
                if (x, y) == bottom_right:
                    continue

                # Find the best path to get to this point
                neighbors = [
                    best_paths[x + xd, y + yd]
                    for xd, yd in ORTHAGONAL
                    if (x + xd, y + yd) in best_paths
                ]

                best_score, best_path = min(neighbors)
                new_score = map[x, y] + best_score
                new_path = [(x, y)] + best_path

                if (x, y) not in best_paths or new_score < best_paths[x, y][0]:
                    best_paths[x, y] = (new_score, new_path)
                    changed_paths += 1

        logging.info(f'Finished iteration, {changed_paths} paths changed')

    return best_paths[0, 0][1]
```

So... did that help?

```bash
$ python3 low-ceiling-simulator.py --version 3 part2 input.txt
best_score=2957
# time 43515557208ns / 43.52s
```

Yes... ish? We have the right answer again and it is about an order of magnitude faster. And it does run in under a minute. So that's probably enough to leave it.

But I know we can do better. After all, there wouldn't happen to be an entire field dedicated to studying exactly these sorts of algorithms, now wouldn't there be?

:smile:

Yeah, I know. I should have just started with A*. It's designed exactly for this sort of thing. Let's start with code this time, then explain it:

```python
def explore_astar(map: Mapping[Point, int]) -> List[Point]:
    '''
    Solve the problem using the A* algorithm.
    '''

    from queue import PriorityQueue

    width = max(x + 1 for (x, _) in map)
    height = max(y + 1 for (_, y) in map)

    start = (0, 0)
    goal = (width - 1, height - 1)

    def h(p):
        return abs(goal[0] - p[0]) + abs(goal[1] - p[1])

    sources: MutableMapping[Point, Tuple[Optional[Point], int]] = {
        start: (None, 0)
    }

    q: PriorityQueue = PriorityQueue()

    q.put((0, start))

    while q:
        logging.info(f'Queue size: {q.qsize()}')

        _, current = q.get()
        (x, y) = current

        if current == goal:
            break

        for xd, yd in ORTHAGONAL:
            next = (x + xd, y + yd)
            if next not in map:
                continue

            new_cost = sources[current][1] + map[current]

            if next not in sources or new_cost < sources[next][1]:
                sources[next] = (current, new_cost)
                q.put((new_cost + h(next), next))

    logging.info(f'Found solution after evaluating {len(sources)} paths')

    best_path = []
    current = goal

    while current:
        best_path.append(current)
        current, score = sources[current]

    best_path = list(reversed(best_path))

    return best_path
```

Okay, so the code is longer, but I don't think it's that much more confusing to read. I think the more confusing part is the guarantee that this *will work*. And that comes down to the heuristic function `h`. So long as `h` is 'admissible' (it will never underestimate the minimum possible cost), you are guaranteed that when you find a solution, it will be optimal. 

And it is *fast*:

```bash
$ python3 low-ceiling-simulator.py --version 4 part2 input.txt
best_score=2957
# time 1903772750ns / 1.90s
```

Yeah... I probably should have just started with that. Oh, and technically all of these algorithms work on part 1 as well:

```bash
$ python3 low-ceiling-simulator.py part1 input.txt
best_score=687
# time 1759175041ns / 1.76s

$ python3 low-ceiling-simulator.py --version 2 part1 input.txt
best_score=687
# time 94618792ns / 0.09s

$ python3 low-ceiling-simulator.py --version 3 part1 input.txt
best_score=687
# time 300569292ns / 0.30s

$ python3 low-ceiling-simulator.py --version 4 part1 input.txt
best_score=687
# time 97045500ns / 0.10s
```

Just less necessary.

Journey before destination and all that. :smile: