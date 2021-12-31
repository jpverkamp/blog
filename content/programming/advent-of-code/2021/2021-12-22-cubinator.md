---
title: "AoC 2021 Day 22: Cubinator"
date: 2021-12-22 00:00:05
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Algorithms
- Mathematics
- Optimization
- Data Structures
---
### Source: [Reactor Reboot](https://adventofcode.com/2021/day/22)

#### **Part 1:** Given a series of 3D cubes that either turn ON all or turn OFF all points in their region, calculate how many points in the region (-50..50,-50..50,-50..50) are ON at the end.

<!--more-->

Wow. This one took me literal days of work to get working for some reason. I actually got to writing unit tests, which is saying something. :D And then after I had one aha moment (changing from cube to edge focussed, see later), it worked basically immediately. Oh data structure choices. 

The basic idea I had all along was to make a `Cube` object that would have all of the operators I need: `a & b` to intersect two cubes, `a | b` (or `a + b`) to union/add them, and `a - b` to subtract one cube from another (each of which will return a list of cubes that make up the result). Then I could:

* Start with an empty list of cubes
* For each cube
    * If ON:
        * Create a sublist of just `[cube]`
        * For each current cube, remove it from every element in the sublist
        * The result is just the new cubes to turn ON, add them to the main list
    * If OFF:
        * For each current cube, remove the new cube from it (generating 0, 1, or many subcubes)

This will be the final list. Let's make that class!

```python
@dataclass(frozen=True, order=True)
class Point:
    x: int
    y: int
    z: int


@dataclass(frozen=True)
class Cube:
    min: Point
    max: Point

    def __repr__(self):
        return f'Cube({len(self)})@[{self.min.x}..{self.max.x}, {self.min.y}..{self.max.y}, {self.min.z}..{self.max.z}]'

    def __len__(self) -> int:
        return (
            (self.max.x - self.min.x)
            * (self.max.y - self.min.y)
            * (self.max.z - self.min.z)
        )
```

These are just the basic methods, print them out and return the 'size' of a cube. One major change I did (entirely too late in the process) was to change from a face-centered system, to an edge centered-system. In that, the original `OldCube(1)@(10..10, 10..10, 10..10)` would be a 1x1 cube including just the point `<10, 10, 10>`, but I changed that so that would be represented by `OldCube(1)@(10..11, 10..11, 10..11)`. The upper bounds are *not* inclusive. That made the math *loads* easier. 

Okay, let's work through the `Cube` methods (they'd all be in one class):

```python
class Cube:
    def __iter__(self) -> Generator[Point, None, None]:
        for x in range(self.min.x, self.max.x):
            for y in range(self.min.y, self.max.y):
                for z in range(self.min.z, self.max.z):
                    yield Point(x, y, z)
```

I didn't actually end up using this, but it can be used to actually get all of the cubes in a point. So if you wanted to directly solve the problem, you could with this!

```python
class Cube
    def __contains__(self, other: Union[Point, 'Cube']) -> bool:
        '''Is the cube/point other entirely contained in self.'''

        if isinstance(other, Point):
            return (
                self.min.x <= other.x <= self.max.x
                and self.min.y <= other.y <= self.max.y
                and self.min.z <= other.z <= self.max.z
            )
        elif isinstance(other, Cube):
            return other.min in self and other.max in self
```

Next, implement `p: Point in c: Cube` and `c1: Cube in c2: Cube`. This is used to special case many of the later methods.

```python
class Cube
    def overlaps(self, other: 'Cube') -> bool:
        '''
        Does the cube overlap with self at all?
        
        Note: This includes if the cubes are just touching since edges are inclusive.
        '''

        return (
            self.min in other
            or self.max in other
            or other.min in other
            or other.max in other
            or self in other
            or other in self
        )
```

The flip side of `in`: do they overlap at all. This could be just touching, but also any number of other cases (partial overlap, to a superset of `in`).

Okay, the heart of all of the next methods:

```python
class Cube:
    def __segment(self, other: 'Cube') -> List['Cube']:
        xs = list(sorted([self.min.x, self.max.x, other.min.x, other.max.x]))
        ys = list(sorted([self.min.y, self.max.y, other.min.y, other.max.y]))
        zs = list(sorted([self.min.z, self.max.z, other.min.z, other.max.z]))

        segments = []

        for i, (x1, x2) in enumerate(zip(xs, xs[1:])):
            for j, (y1, y2) in enumerate(zip(ys, ys[1:])):
                for k, (z1, z2) in enumerate(zip(zs, zs[1:])):
                    new_segment = Cube(Point(x1, y1, z1), Point(x2, y2, z2))

                    if new_segment in segments:
                        continue

                    segments.append(new_segment)

        return segments
```

The idea of this method is that any two cubes can be divided into 3x3 = 27 'segments', no matter how they overlap. If they overlap on a corner, the middle of those will be the middle segment. If they only touch, then the touching line will be a zero size middle segment. If they don't touch at all, the middle segment will be 'between' the cubes.

This is the method that benefited the most from the rewrite to edge-focused cubes. Before that, I had to have all sorts of special cases where you didn't accidentally include the edge cubes twice. With the change... it's just this much code.

Now that we have that, we can implement `&`, `|`, `+`, and `-` as various combinations of `__segment` and `in`:

```python
class Cube:
    def __and__(self, other: 'Cube') -> List['Cube']:
        '''Calculate the list of cubes making up the intersection of self and other.'''

        # One cube is entirely inside of the other
        if self in other:
            return [self]
        elif other in self:
            return [other]

        # No overlap at all
        elif not self.overlaps(other):
            return []

        # Finally, only segments that are in both
        else:
            return Cube.compress([
                segment
                for segment in self.__segment(other)
                if segment in self and segment in other
            ])

    def __or__(self, other: 'Cube') -> List['Cube']:
        '''Calculate the list of cubes making up the union of self and other.'''

        # One cube is entirely inside the other
        if self in other:
            return [other]
        elif other in self:
            return [self]

        # No overlap at all
        elif not self.overlaps(other):
            return [self, other]

        # Otherwise, split into segments and return all of them
        else:
            return Cube.compress([
                segment
                for segment in self.__segment(other)
                if segment in self or segment in other
            ])

    def __add__(self, other: 'Cube') -> List['Cube']:
        '''Adding is the same as intersection.'''

        return self | other

    def __sub__(self, other: 'Cube') -> List['Cube']:
        '''Calculate the list of cubes resulting of removing other from self.'''

        # Subtract the entire thing
        if self in other:
            return []

        # No overlap at all
        elif not self.overlaps(other):
            return [self]

        return Cube.compress([
            segment
            for segment in self.__segment(other)
            if segment in self and segment not in other
        ])
```

Pretty sweet how clean that code is. But ... what's that compress thing? It's not necessary to actually solve the problem, but what it does is make the number of cubes explode slightly less. Rather than up to 27 new cubes, if any of the new cubes can be combined (by glueing one face together), do it:

```python
class Cube:
    def join(self, other: 'Cube') -> Optional['Cube']:
        '''If two cubes can be perfectly joined, return that.'''

        # One cube contains the other
        if self in other:
            return other
        elif other in self:
            return self

        # The x/y/z edges match perfectly
        x_match = self.min.x == other.min.x and self.max.x == other.max.x
        y_match = self.min.y == other.min.y and self.max.y == other.max.y
        z_match = self.min.z == other.min.z and self.max.z == other.max.z

        # The last dimension is contained within the other cube
        x_overlap = (
            (other.min.x <= self.min.x <= other.max.x)
            or (other.min.x <= self.max.x <= other.max.x)
            or (self.min.x <= other.min.x <= self.min.x)
            or (self.min.x <= other.max.x <= self.min.x)
        )

        y_overlap = (
            (other.min.y <= self.min.y <= other.max.y)
            or (other.min.y <= self.max.y <= other.max.y)
            or (self.min.y <= other.min.y <= self.min.y)
            or (self.min.y <= other.max.y <= self.min.y)
        )

        z_overlap = (
            (other.min.z <= self.min.z <= other.max.z)
            or (other.min.z <= self.max.z <= other.max.z)
            or (self.min.z <= other.min.z <= self.min.z)
            or (self.min.z <= other.max.z <= self.min.z)
        )

        # If we have exactly two matches and an overlap, we can combine
        if (
            (x_overlap and y_match and z_match)
            or (x_match and y_overlap and z_match)
            or (x_match and y_match and z_overlap)
        ):
            result = Cube(min(self.min, other.min), max(self.max, other.max))
            return result

        return None

    @staticmethod
    def compress(cubes: List['Cube']) -> List['Cube']:
        '''Take a list of cubes and join as many as we can.'''

        cubes = list(cubes)

        def find_one_join():
            for i, c1 in enumerate(cubes):
                for j, c2 in enumerate(cubes):
                    if j <= i:
                        continue

                    if c := c1.join(c2):
                        return i, j, c

        while True:
            if result := find_one_join():
                i, j, c = result

                del cubes[j]
                del cubes[i]
                cubes.append(c)
            else:
                break

        return cubes
```

It's... something that came about when fiddling with the old cube-centered mess, but it still does help. 

So what's the final algorithm look like?

```python
def read(file: TextIO) -> Generator[Tuple[bool, Cube], None, None]:
    for line in file:
        m = re.match(r'(on|off) x=(-?\d+)\.\.(-?\d+),y=(-?\d+)\.\.(-?\d+),z=(-?\d+)\.\.(-?\d+)', line)
        if m:
            mode, x1, x2, y1, y2, z1, z2 = m.groups()
            cube = Cube(
                Point(int(x1), int(y1), int(z1)),
                Point(int(x2) + 1, int(y2) + 1, int(z2) + 1)
            )

            yield mode == 'on', cube


@app.command()
def main(file: typer.FileText, limit: bool = False):
    cubes: List[Cube] = []

    for turn_on, cube in read(file):
        logging.info(f'{turn_on=} {cube=}')

        # Turning on cubes, don't turn on anything that is already on
        if turn_on:
            to_turn_on = [cube]

            for old_cube in cubes:
                to_turn_on = [
                    remaining_cube
                    for to_turn_on_cube in to_turn_on
                    for remaining_cube in to_turn_on_cube - old_cube
                ]

            cubes += to_turn_on

        # Turning off cubes, turn off anything that should be off
        else:
            cubes = [
                reduced_cube
                for current_cube in cubes
                for reduced_cube in current_cube - cube
            ]

        # Re-compress at the end of each cycle
        cubes = Cube.compress(cubes)

        logging.info(f'''\
After {turn_on=} {cube=}: {len(cubes)=}, {sum(len(cube) for cube in cubes)=}
''')

        # Remove all regions outside of -50..50
        # This is silly, because we'll need to keep them in part 2
        # But it's faster at least
        if limit:
            cubes = Cube.compress([
                reduced
                for cube in cubes
                for reduced in cube & Cube(Point(-50, -50, -50), Point(51, 51, 51))
            ])

    print(sum(len(cube) for cube in cubes))

@app.command()
def part1(file: typer.FileText):
    main(file, True)
```

Almost exactly what I described in the pseudo-code, albeit a bit longer. It's kind of funny, because we need to remove the -50..50 region even though we already calculated it. It does run quicker without it though:

```bash
$ python3 cubinator.py part1 input.txt
590467
# time 33116921042ns / 33.12s
```

#### **Part 2:** Do the same without the -50..50 limit.

```python
@app.command()
def part2(file: typer.FileText):
    main(file, False)
```

Yeah... it takes forever.

```bash
$ python3 cubinator.py part2 input.txt
1225064738333321
# time 9420109196167ns / 9420.11s
```

Yeah. That's 2hrs 37mins. But after working so long on this problem... I'm done. :D

I am going to look at what algorithms other people used, because this one was kind of crazy...

(And apparently I didn't manage to actually push these... sadness)

#### Optimization: Caching

Everything in this problem is immutable, so I can use `@cache` all over the place on `Cube`'s methods. Unfortunately, there's not really that much overlap in the questions you ask:

```python
--- Day 22: Reactor Reboot ---

$ python3 cubinator.py part1 input.txt
590467
# time 35257615584ns / 35.26s

$ python3 cubinator.py --cache part1 input.txt
590467
# time 35879987167ns / 35.88s
```

Perhaps on the longer problem... but yeah, that already takes long enough, I don't really want to re-run it with caching.

```bash
$ python3 cubinator.py --debug --cache part2 input.txt

12:45:47 INFO 0001: turn_on=True cube=Cube(105938)@[-40..7, -36..10, -36..13]
12:45:47 INFO       len(cubes)=1, sum(len(cube) for cube in cubes)=105938

12:45:47 INFO 0002: turn_on=True cube=Cube(133650)@[-22..32, -48..7, -35..10]
12:45:47 INFO       len(cubes)=3, sum(len(cube) for cube in cubes)=183473

...

15:19:41 INFO 0419: turn_on=False cube=Cube(6643764051090)@[-80436..-61650, 3782..34677, 22972..34419]
15:21:00 INFO       len(cubes)=3139, sum(len(cube) for cube in cubes)=1228724794372331

15:21:00 INFO 0420: turn_on=False cube=Cube(9585355541608)@[-62269..-36062, -15314..13682, 65100..77714]
15:21:22 INFO       len(cubes)=3152, sum(len(cube) for cube in cubes)=1225064738333321

1225064738333321
```

Also... 2hrs 36mins. That's actually impressively consistent if anything. Not so great on the caching though. 

#### Optimization: Block turn 'on' together

A sequence of turn on options in a row can all be done together. I'm not sure if this would help with the overall performance, but worth a try?

#### Optimiation: Octree

One thing that I think would really work for this problem would be to use {{< wikipedia "octrees" >}}. Rather than representing a list of cubes, we could split the entire space into one giant octree. Then when we need to break apart a given cube, we can do so with the built in octree stuff and not have to check every cube against every other cube (that gets *very* expensive). The hardest bit to get right would probably be once cubes span multiple nodes (at multiple levels of the octree). Worth considering though?