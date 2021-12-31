---
title: "AoC 2021 Day 12: Submarine Spider"
date: 2021-12-12 00:00:15
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
- Data Structures
---
### Source: [Passage Pathing](https://adventofcode.com/2021/day/12)

#### **Part 1:** Given a list of edges in a bi-directional graph, count the number of paths from `start` to `end` such that nodes named with lowercase letters are visited once, and nodes with uppercase letters can be visited any number of times. 

<!--more-->

Interesting. First, let's define a graph structure:

```python
@dataclass(frozen=True)
class Node:
    label: str

    def is_big(self):
        return self.label.isupper()

    def __repr__(self):
        return f'<{self.label}>'


@dataclass(frozen=True)
class Cave:
    edges: Mapping[Node, Set[Node]]

    @staticmethod
    def from_file(file: TextIO):

        edges: Dict[Node, Set[Node]] = {}

        for line in file:
            nodes = [Node(v) for v in line.strip().split('-')]

            for node in nodes:
                if node not in edges:
                    edges[node] = set()

            for node_a in nodes:
                for node_b in nodes:
                    if node_a != node_b:
                        edges[node_a].add(node_b)

        # Convert to a dict
        return Cave(edges)
```

Originally, I had the pathing function in this class directly, but because it changes for part 2, I extracted it into the part 1 function:

```python
def part1(file: typer.FileText):
    cave = Cave.from_file(file)

    def paths(node: Node, visited: Set[Node]) -> Generator[List[Node], None, None]:
        '''Yield all possible paths from the given node to <end>.'''

        if node == END:
            yield [END]
            return

        if node.is_small() and node in visited:
            return

        for next in cave.edges[node]:
            for path in paths(next, visited | {node}):
                yield [node] + path

    count = 0
    for _ in paths(START, set()):
        count += 1

    print(count)
```

Because the paths are short enough, we can get away with a simple recursive function. In this case, `paths` will take the current point in the graph and a list of nodes visited already (so that we can avoid lowercase nodes that we've already visited) and generate all paths from that point. It does so by recursion: each step is moving to a neighboring node in the graph, we're assuming the recursive call will generate some number of paths (might be 0), and the base case is the `end` node.

Note: If there are ever two or more 'big' nodes adjacent to each other, this will totally blow up, since you can infinitely loop between the two. Good thing that doesn't come up in our input. :D This could be fixed with {{< wikipedia "cycle detection" >}}, but that would make teh algorithm somewhat slower...

```bash
$ python3 submarine-spider.py part1 input.txt
4749
```

#### **Part 2:** Repeat Part 1, but you are allowed to visit a single lowercase node more than once (although you do not have to). Count the number of paths. 

Like I said, a tweak to the `paths` function:

```python
@app.command()
def part2(file: typer.FileText):
    cave = Cave.from_file(file)

    def paths(node: Node, visited: Set[Node], used_double: bool) -> Generator[List[Node], None, None]:
        '''Yield all possible paths from the given node to <end>.'''

        if node == END:
            yield [END]
            return

        if node == START and START in visited:
            return

        if node.is_small() and node in visited and used_double:
            return

        for next in cave.edges[node]:
            for path in paths(next, visited | {node}, used_double or (node.is_small() and node in visited)):
                yield [node] + path

    count = 0
    for _ in paths(START, set(), False):
        print(_)
        count += 1

    print(count)
```

Yeah... it's a fair bit more complicated this time, but with the code + comments, I think it makes sense. The most interesting is the last/`any` case. In that case, we have to check if we've *already* double visited a small node, because if so, we can't do it again. 

Running it:

```bash
$ python3 submarine-spider.py part2 input.txt
123054
```

Wow. That's quite a lot more.

#### Performance

```bash
--- Day 12: Passage Passing ---

$ python3 submarine-spider.py part1 input.txt
4749
# time 69264250ns / 0.07s

$ python3 submarine-spider.py part2 input.txt
123054
# time 1300497125ns / 1.30s
```

So... that's not the end of the world, but it's still much slower than it could be. One thing that we should be able to is use {{< wikipedia "memoization" >}} to 'remember' each path from a given point, so we can avoid computing them more than once. Unfortunately, that seems to mean that we cannot use a generator. 

```python
def part2_fast(file: typer.FileText):
    cave = Cave.from_file(file)

    @cache
    def paths(node: Node, visited: FrozenSet[Node], used_double: bool) -> List[List[Node]]:
        '''Yield all possible paths from the given node to <end>.'''

        if node == END:
            return [[END]]

        if node == START and START in visited:
            return []

        if node.is_small() and node in visited and used_double:
            return []

        return [
            [node] + path
            for next in cave.edges[node]
            for path in paths(next, visited | {node}, used_double or (node.is_small() and node in visited))
        ]

    count = 0
    for _ in paths(START, frozenset(), False):
        count += 1

    print(count)
```

Instead of the generator, we return the list of solutions, so we can {{< doc python "functools.cache" >}} it. That's pretty neat and a bit faster:

```bash
$ python3 submarine-spider.py part2 input.txt
123054
# time 1300497125ns / 1.30s

$ python3 submarine-spider.py part2-fast input.txt
123054
# time 564378250ns / 0.56s
```

It's still doing a lot of messy list copying and appending. I think we could do better, but for now, it's at least under a second...
