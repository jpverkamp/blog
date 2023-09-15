---
title: "AoC 2021 Day 5: Linear Avoidinator"
date: 2021-12-05 00:00:10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Hydrothermal Venture](https://adventofcode.com/2021/day/5)

#### **Part 1:** Given a list of lines, find the number of integer points which are covered by more than one line (ignore non-vertical and non-horizontal lines). 

Okay. Start with the data structures:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Line:
    p1: Point
    p2: Point

    def is_vertical(self):
        return self.p1.x == self.p2.x

    def is_horizontal(self):
        return self.p1.y == self.p2.y

    def is_orthagonal(self):
        return self.is_vertical() or self.is_horizontal()

    def points(self):
        # TODO: handle lines that aren't vertical, horizontal, or diagonal

        xd = 0 if self.p1.x == self.p2.x else (1 if self.p1.x < self.p2.x else -1)
        yd = 0 if self.p1.y == self.p2.y else (1 if self.p1.y < self.p2.y else -1)

        p = self.p1
        while p != self.p2:
            yield p
            p = Point(p.x + xd, p.y + yd)

        yield p
```

Dataclasses are great. They give you constructors and a bunch of other things for free. On top of that, if you specify `frozen=True`, making them immutable, you also get `hashable` types for free (which I'll use in the problem). 

Perhaps the most interesting bit here is the function that will iterate through the `points` in a `List`. Specifically, it will figure out the x and y delta (`xd` and `yd`) and repeatedly add that until you hit the end point. 

**Note:** this only works for lines that are vertical, horizontal, or diagonal (at 45 degrees). Anything else needs a better [[wiki:line drawing algorithm]]() (of which there are a few). If we need it, I'll implement it. 

Next, use that to parse:

```python
def parse(file: TextIO) -> List[Line]:
    result = []

    for line in file:
        x1, y1, x2, y2 = [int(v) for v in line.replace(' -> ', ',').split(',')]
        result.append(Line(Point(x1, y1), Point(x2, y2)))

    return result
```

The input format is `x1,y1 -> x2,y2`, but it's easier to split and convert if we do it all directly. There are a few other ways we could have done this: splitting on anything non-numeric or using a regular expression / something else for parsing directly. But I think this is clear enough. 

And with all that, the problem is actually pretty short:

```python
def part1(file: typer.FileText):

    lines = parse(file)
    counter: MutableMapping[Point, int] = collections.Counter()

    for line in lines:
        if not line.is_orthagonal():
            continue

        for point in line.points():
            counter[point] += 1

    print(sum(1 if count > 1 else 0 for point, count in counter.items()))
```

We'll use the built in `collections.Counter` datatype, since that's exactly what we're doing: counting things. Then just iterate over every line, skip the non-orthagonal ones, iterate over every point, and count them up. At the end, print the number that we saw more than once. Et voila. 

```bash
$ python3 linear-avoidinator.py part1 input.txt
5632
```

<!--more-->

#### **Part 2:** Repeat, also including lines at 45 degrees. 

That's actually easier, since I already did the work to calculate diagonal lines when I wrote the `Line` class. Just drop the `is_orthagonal` clause:

```python
def part2(file: typer.FileText):

    lines = parse(file)
    counter: MutableMapping[Point, int] = collections.Counter()

    for line in lines:
        for point in line.points():
            counter[point] += 1

    print(sum(1 if count > 1 else 0 for point, count in counter.items()))
```

And run it:

```python
$ python3 linear-avoidinator.py part2 input.txt
22213
```

Not bad.

#### Timing

```bash
--- Day 5: Hydrothermal Venture ---

$ python3 linear-avoidinator.py part1 input.txt
5632
# time 170506875ns / 0.17s

$ python3 linear-avoidinator.py part2 input.txt
22213
# time 298739417ns / 0.30s
```

Okay, we're starting to slow down. Iterating through a whole bunch of points, creating new objects for each, and storing all that in a `Counter` is not super efficient. But if it runs in a second on the largest data set we're practically going to throw at it... 

:shrug: 

I'm perfectly all right with anything under a second and once problems get harder, I probably won't fight too hard if they stay under a minute unless optimizing is unusually interesting. After that, I'll probably spend some time on it. 