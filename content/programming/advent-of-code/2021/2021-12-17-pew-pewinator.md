---
title: "AoC 2021 Day 17: Pew-Pewinator"
date: 2021-12-17
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Trick Shot](https://adventofcode.com/2021/day/17)

#### **Part 1:** Simulate a projectile with an integer initial velocity (x, y), air resistance that tries to reduce x-velocity to 0, and gravity that increases y-velocity by 1 each time. Given a target range, find the highest point reached by a projectile that ends a tick (not one that crosses over) within the target area. 

<!--more-->

Oh goodness, this one got weird. Let's start with data structures. A point:

```python
@dataclass(frozen=True)
class Point:
    '''Represents a point in 2-space, positive y is up'''

    x: int
    y: int
```

A rectangular target with loading a specific format and the ability to determine if a point is in that rectangle:

```python
@dataclass(frozen=True)
class Rect:
    '''Represents a rectangle in 2-space, positive Y is up'''

    position: Point
    width: int
    height: int

    @staticmethod
    def from_file(file: TextIO):
        m = re.match(
            r'target area: x=(-?\d+)\.\.(-?\d+), y=(-?\d+)\.\.(-?\d+)',
            file.readline()
        )

        if m:
            x1, x2, y1, y2 = m.groups()
            return Rect(
                Point(int(x1), int(y1)),
                int(x2) - int(x1),
                int(y2) - int(y1)
            )

    def __contains__(self, p: Point):
        return (
            self.position.x <= p.x <= self.position.x + self.width
            and self.position.y <= p.y <= self.position.y + self.height
        )
```

This caused some issues, since an example target of `target area: x=20..30, y=-10..-5` *should* include the point `30, -7` for example. As they say, the two hardest things in computer science are caching, naming things, and off by one errors. :smile:

And finally, the probe itself:

```python
@dataclass(frozen=True)
class Probe:
    '''Represents a probe with initial position and velocity.'''

    position: Point
    velocity: Point

    def update(self) -> 'Probe':
        return Probe(
            position=Point(
                self.position.x + self.velocity.x,
                self.position.y + self.velocity.y
            ),
            velocity=Point(
                self.velocity.x + (1 if self.velocity.x < 0 else -1 if self.velocity.x > 0 else 0),
                self.velocity.y - 1
            )
        )

    def impacts(self, target: Rect) -> Optional[int]:
        '''
        Tests if the given probe hits the given target.

        If yes: return the maximum height reached (the coolness factor)
        If no: return None
        '''

        current = self
        coolness = self.position.y

        while current.position.y >= target.position.y:
            if current.position in target:
                return coolness

            current = current.update()
            coolness = max(coolness, current.position.y)

        return None
```

I made the (admittedly a bit odd for Python) decision for this to be an immutable data structure. That means that `update` doesn't change the Probe itself, but rather returns a new updated Probe. It doesn't change that much, but it does change a bit. 

Okay, next up, we want to find all of the possible points that could impact. I expect the best way to do this would be to solve the various kinematic equations and find the single/two best answers, but where's the fun in that? Instead, I'm going to try *every* possible projectile.

There's a bit of a caveat to that though, because you don't want to just keep going on forever. So instead, what I did was start at an initial velocity of `(0, 0)` (just let the probe drop) and then scan 'outwards'. So `(0, -1)`, `(1, 0)`, and `(0, 1)`. Then all 2 distance ones, etc. Eventually, we would start hitting the target... and the assumption was that once we stopped hitting it for an entire offset, we would be done.

Turns out, that wasn't quite correct. There are actually multiple sets of answers. For example, those that lob the probe really high up (high initial velocity) and those that aim lower or even down. Once you've found all the sets though, you're done:

```python
def all_impacts(target: Rect, phases: int = 2) -> Generator[Tuple[Probe, int], None, None]:
    logging.info(f'all_impacts({target=}), starting')

    origin = Point(0, 0)
    phase = 0

    # Original thoughts:

    # Even phases mean that you haven't seen an impact yet
    # Odd phases mean you're currently scanning an 'impact zone'

    # Since there are two 'impact zones', you should expect to go through:
    # 0: before any impacts
    # 1: first impact zone
    # 2: between the zones
    # 3: second impact zone
    # 4: done scanning

    # Later thoughts:
    # Apparently there are 6 blocks of solutions total...

    for offset in itertools.count(1):
        logging.info(f'all_impacts({target=}), {offset=}, {phase=}')

        at_least_one_impact = False

        for xd in range(offset+1):
            for yd in range(-offset, offset+1):
                if abs(xd) + abs(yd) != offset:
                    continue

                probe = Probe(origin, Point(xd, yd))
                coolness = probe.impacts(target)

                if coolness is not None:
                    logging.info(f'all_impacts({target=}), Hit! {xd=}, {yd=} -> {coolness=}')
                    yield(probe, coolness)

                    at_least_one_impact = True

        if phase % 2 == 0 and at_least_one_impact:
            phase += 1
        elif phase % 2 == 1 and not at_least_one_impact:
            phase += 1

        if phase == phases * 2:
            break
```

And ... that seems to work well enough, so let's find the highest flying probe:

```python
def part1(file: typer.FileText):

    target = Rect.from_file(file)
    logging.info(target)

    most_cool = None

    for probe, coolness in all_impacts(target):
        if most_cool is None or coolness > most_cool:
            logging.info(f'part1: New coolest impact! {probe=}, {coolness=}')
            most_cool = coolness

    print(most_cool)
```

Feel like cheating.

```bash
$ python3 pew-pewinator.py part1 input.txt
2850
# time 729939625ns / 0.73s
```

Quick enough at least. 

#### **Part 2:** Count the number of *all* possible initial velocities (x, y) that end up in the target. 

Well, we already did that. Does it have the right answer?

```python
def part2(file: typer.FileText):

    target = Rect.from_file(file)
    logging.info(target)

    valid_probes = []

    for probe, coolness in all_impacts(target, 5):
        valid_probes.append(probe)

    logging.info('All valid probes:')
    for probe in valid_probes:
        logging.info(probe)

    print(len(valid_probes))
```

It's ugly... and I have no really good reason for why there are 5 sets of solutions. I should graph the phase space. 

```bash
$ python3 pew-pewinator.py part2 input.txt
1117
# time 34581116542ns / 34.58s
```

And it's slow. I may come back to this one... but not for now. 

