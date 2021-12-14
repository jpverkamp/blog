---
title: "AoC 2021 Day 13: Foldinator"
date: 2021-12-13
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Transparent Origami](https://adventofcode.com/2021/day/13)

#### **Part 1:** Given a set of points and a sequence of 'fold' lines (where you either fold the bottom over the top or right over left), determine how many points exist after the first fold. 

First, data structures:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f'<{self.x}, {self.y}>'


@dataclass(frozen=True)
class Fold:
    horizontal: bool
    line: int

    def apply_to(self, points: Set[Point]) -> Set[Point]:
        return {
            Point(
                p.x if (self.horizontal or p.x < self.line) else self.line * 2 - p.x,
                p.y if (not self.horizontal or p.y < self.line) else self.line * 2 - p.y
            )
            for p in points
        }

    def __repr__(self):
        return f'fold@{"x" if self.horizontal else "y"}={self.line}'
```

Yes. Those could (mostly) be tuples. But I happen to like putting them in their own classes. The `apply_to` method is actually the bulk of the functionality here. 

What you need to consider is when the `x`/`y` of a point *do not* change. If you're folding a horizontal line, the `x` will *never* change (likewise for vertical and `y`). Also, if you're in the top or left half, you'll not change. 

There's only 1 in 4 cases that change: if you're below/right of the fold that's changing. 

In that case, you are going to reflect it. In this case, if you're folding a point with `y=14` over the line `y=7`, then you should end up with `1`. Thus `line*2-y`. 

Next, two helper functions in order to load/print the current points:

```python
def load(file: TextIO) -> Tuple[Set[Point], List[Fold]]:
    points = set()
    folds = []

    for line in file:
        if ',' in line:
            xs, ys = line.split(',')
            points.add(Point(x=int(xs), y=int(ys)))

        elif '=' in line:
            left, vs = line.split('=')
            folds.append(Fold(horizontal=left.endswith('y'), line=int(vs)))

    return points, folds

def render(points: Set[Point]):
    width = max(p.x + 1 for p in points)
    height = max(p.y + 1 for p in points)

    print('\n'.join(
        ''.join(
            '*' if Point(x, y) in points else ' '
            for x in range(width)
        )
        for y in range(height)
    ))
    print()
```

Straight forward enough. Technically, this is a more flexible format than given (you can mix points and folds in any order), but that's a superset of what we're actually interested in, so good enough. 

Now that we have all of that, we can actually do all of the folds... but we only need the first:

```python
def part1(file: typer.FileText):
    points, folds = load(file)
    points = folds[0].apply_to(points)
    print(len(points))
```

So short. :smile:

```bash
$ python3 foldinator.py part1 input.txt
706
```

Heh. 

<!--more-->

#### **Part 2:** After all defined folds, what letters are revealed?

We've already done all of this while testing part 1, so on we go!

```python
@app.command()
def part2(file: typer.FileText):
    points, folds = load(file)

    for fold in folds:
        points = fold.apply_to(points)

    render(points)
```

That seems like cheating, but does it work?

```bash
$ python3 foldinator.py part2 input.txt
*    ***  ****   ** ***    ** **** *  *
*    *  * *       * *  *    * *    *  *
*    *  * ***     * ***     * ***  ****
*    ***  *       * *  *    * *    *  *
*    * *  *    *  * *  * *  * *    *  *
**** *  * *     **  ***   **  **** *  *
```

Fun! 

I could write something to turn those into an actual string, but ... nah, not right now. 

That's it for today. Fun one!