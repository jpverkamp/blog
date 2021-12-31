---
title: "AoC 2021 Day 19: Point Matchinator"
date: 2021-12-19 00:00:05
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Data Structures
- Mathematics
---
### Source: [Snailfish](https://adventofcode.com/2021/day/19)

#### **Part 1:** You will be given a series of Scanners, each of which will tell you the location (from their point of view) of a series of Beacons. Each Scanner may be flipped or rotated in increments of 90 degrees in any direction. Determine where each Scanner and Beacon is by overlaying the maps (with at least pairwise 12 matches). 

<!--more-->

That... was quite a problem to get right. It's a lot of match to make sure that the various coordinate systems can be converted between one another and computationally expensive to brute force. I haven't gotten this one much below 10 minutes... but at this point, I'm just going to have to call it. It's a crazy problem. 

Okay. Let's start with a 3-dimensional point:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int
    z: int

    def __repr__(self):
        return f'{{{self.x}, {self.y}, {self.z}}}'

    @staticmethod
    def all_waggles() -> Generator['Point', None, None]:
        '''Generate all waggle parameters (see Point.waggle)'''

        for i, j, k in itertools.permutations((1, 2, 3)):
            for ix in (-i, i):
                for jx in (-j, j):
                    for kx in (-k, k):
                        yield Point(ix, jx, kx)

    def waggle(self, w: 'Point') -> 'Point':
        '''
        Return a new point reflected/reordered by the given coordinates.

        Each of w's x,y,z should be +- 1,2,3 and each of 1,2,3 should be used exactly once.

        reflect(3, 2, -1) should return Point(z, y, -x) for example.
        '''

        d = (-1, self.x, self.y, self.z)

        return Point(
            d[abs(w.x)] * (-1 if w.x < 0 else 1),
            d[abs(w.y)] * (-1 if w.y < 0 else 1),
            d[abs(w.z)] * (-1 if w.z < 0 else 1),
        )

    def __add__(self, other: 'Point') -> 'Point':
        '''Return the sum of two points.'''

        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Point') -> 'Point':
        '''Return the difference of two points, obv.'''

        return Point(self.x - other.x, self.y - other.y, self.z - other.z)
```

Waggle? Waggle. Basically, that's the name I'm using for flipping and mirroring about any of x/y/z. Specifically, any ordering of `(1, 2, 3)` (each can be positive or negative) to re-order the coordinates and possibly flip them around. That ends up with the 24 possible orientations (`all_waggles`). 

Next, Scanners:

```python
@dataclass(frozen=True)
class Scanner:
    name: str
    points: FrozenSet[Point]

    @staticmethod
    def read(file: TextIO) -> Optional['Scanner']:
        '''Read a Scanner from a filelike object'''

        if not (name := file.readline().strip('- \n')):
            return None

        points = set()
        while line := file.readline().strip():
            points.add(Point(*[int(v) for v in line.split(',')]))

        return Scanner(name, frozenset(points))

    def __or__(self, other: 'Scanner') -> Optional[Tuple[Point, Point, Set[Point]]]:
        '''Given another scanner, try to find the overlapping points.'''

        # Try every waggle of their scanners, assume I'm always right
        for their_waggle in Point.all_waggles():
            their_waggled_points = {
                p.waggle(their_waggle)
                for p in other.points
            }

            logging.debug(f'Comparing {self.points=} and {their_waggled_points=}')

            # Choose where we think the 'other' scanner is from our perspective
            for my_zero in self.points:
                my_zeroed_points = {p - my_zero for p in self.points}

                for their_waggled_zero in their_waggled_points:
                    their_zeroed_points = {p - their_waggled_zero for p in their_waggled_points}

                    # Try to subtract that from all of our points
                    # If we have enough matches, that means we know their scanner from our point of view
                    matches = my_zeroed_points & their_zeroed_points

                    if len(matches) >= BEACON_OVERLAPPINGNESS:
                        return (their_waggle, my_zero - their_waggled_zero, {p + my_zero for p in matches})

        return None

    def __repr__(self):
        return f'@{{{self.name}}}'
```

I don't know why I used `s0 | s1` as the operator for overlapping two scanners... but I did. Yay dunder methods? 

The method here is actually pretty neat. Essentially, the matching algorithm is:

* Try every possible `waggle` (orientation that the other Scanner could be at)
* Try every possible point from each scanner as the '`zero`' (the point at which we've overlapping), `other` has to have their `zero` waggled
* Calculate the offsets from the zero for each
* If the `waggle` is correct (so that both Scanners are now facing the same way) and the `zeros` actually match... we're golden. We'll have at least 12 matches and can return
* Calculate the points that overlapped along with the `waggle` necessary to convert between the zones

That last step took... rather a while to get right. And all because of a much lower level bug up in the `their_waggled_points` part. Man it's hard to debug bad data. Garbage in, garbage out. That's still a neat algorithm though. 

Next... let's combine these and try to figure out how to actually calculate all of the Beacons.

First, load the input and find initial mappings between every pair of Scanners. This is... horribly inefficient. I did at least make sure that if I do `[s0, s1]`, then I don't have to do `[s1, s0]` (they're the same). But otherwise, I really am going through all of them.

```python
scanners = []
while s := Scanner.read(file):
    scanners.append(s)
s0 = scanners[0]

logging.info('=== FINDING INITIAL OFFSETS ===')
offsets: MutableMapping[Tuple[Scanner, Scanner], Tuple[Point, Point, Set[Point]]] = {}

for s0 in scanners:
    for s1 in scanners:
        logging.info(f'Finding the offset from {s0=} to {s1=}')

        if (s1, s0) in offsets:
            offsets[s0, s1] = offsets[s1, s0]

        if result := (s0 | s1):
            offsets[s0, s1] = result
```

That will find Unfortunately, not every pair overlaps. So we can go from 0 to 1 and 1 to 4, but not directly from 0 to 4. And we want to be able to do that, to make sure we have *everything* in the same universal coordinate system. So next:

```python
# Fill in the entire chart
logging.info('=== EXPANDING CHART ===')
s0 = scanners[0]

# If we don't have a path from s0 to s1, try to go s0 -> svia -> s1
updating = True
while updating:
    logging.info('Working on expanding iteration')
    updating = False

    for s1 in scanners[1:]:
        if (s0, s1) in offsets:
            continue

        for svia in scanners[1:]:
            if s0 == svia or svia == s1:
                continue

            if not ((s0, svia) in offsets and (svia, s1) in offsets):
                continue

            logging.info(f'Building a new path from {s0} via {svia} to {s1}')

            waggle1, offset1, _ = offsets[s0, svia]
            waggle2, offset2, points2 = offsets[svia, s1]

            new_waggle = waggle2.waggle(waggle1)
            new_offset = offset1 + offset2.waggle(waggle1)

            new_points = {
                offset1 + p.waggle(waggle1)
                for p in points2
            }

            offsets[s0, s1] = new_waggle, new_offset, new_points
            updating = True
```

Getting that `new_points` right took a bit too. And it's all so simple... I enjoy naming things.

And that's mostly it. Go through now that we know the `offset` and `waggle` for every Scanner, we can actually map all of the Beacons they'd seen into the same coordinate space and de-duplicate:

```python
def part1(file: typer.FileText):

    scanners = []
    while s := Scanner.read(file):
        scanners.append(s)
    s0 = scanners[0]

    offsets = do_the_actual_work(scanners)

    # Finally, calculate all of the beacon points
    logging.info('=== FINDING BEACONS ===')

    all_beacons = set()
    for scanner in scanners:
        waggle, offset, _ = offsets[s0, scanner]
        logging.info(f'Adding beacons from {scanner} at {offset} (with {waggle=})')

        all_beacons |= {
            offset + p.waggle(waggle)
            for p in scanner.points
        }

    print(len(all_beacons))
```

And that's it!

```bash
$ python3 point-matchinator.py part1 input.txt
313
# time 412607815209ns / 412.61s
```

Yeah. That's slow. But it works and at this point, that's enough for me. 

#### **Part 2:** Find the largest Manhattan Distance between any two Scanners. 

This actually doesn't need any more work. Just use the data we have and calculate the distances. That part is fast.

```python
def part2(file: typer.FileText):

    scanners = []
    while s := Scanner.read(file):
        scanners.append(s)
    s0 = scanners[0]

    offsets = do_the_actual_work(scanners)

    # Finally, calculate all of the beacon points
    logging.info('=== FINDING SCANNERS ===')

    locations = set()
    for scanner in scanners:
        _, offset, _ = offsets[s0, scanner]
        locations.add(offset)

    print(max(
        abs(l1.x - l2.x) + abs(l1.y - l2.y) + abs(l1.z - l2.z)
        for l1 in locations
        for l2 in locations
    ))
```

It's no faster since I'm still `doing_all_the_actual_work`, but if I'm doing both parts, I could at least cache it. For now, onwards and good enoughwards. 

```bash
$ python3 point-matchinator.py part2 input.txt
10656
# time 397226430042ns / 397.23s
```