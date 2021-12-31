---
title: "AoC 2021 Day 23: Amphipodinator"
date: 2021-12-23 00:00:03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Algorithms
- Optimization
- A-Star
---
### Source: [Amphipod](https://adventofcode.com/2021/day/23)

#### **Part 1:** Given 4 rooms full of amphipods with various energy costs for movement (a=1, b=10, c=100, d=1000) and a hallway, how much energy does it take (at minimum) to sort the amphipods into their own rooms with the following conditions:

<!--more-->

* Amphipods will move from rooms into the hallway, but will not stop on the space immediately outside of any room
* Amphipods will not enter a room other than their own
* Amphipods will not enter a room that has other kinds of amphipods in it
* Amphipods will only move from the hallway into a room

There's an interesting caveat in the last two points, but we'll come back to that. 

So let's start by getting these things loaded in:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f'<{self.x}, {self.y}>'

    def distance(self, other: 'Point'):
        return abs(other.x - self.x) + abs(other.y - self.y)


@dataclass(frozen=True)
class State:
    width: int
    height: int
    walls: FrozenSet[Point]
    amphipods: Mapping[str, FrozenSet[Point]]

    @staticmethod
    def read(file: TextIO):

        width = 0
        height = 0
        walls = set()
        amphipods = {}

        for y, line in enumerate(file):
            height = max(y + 1, height)

            for x, c in enumerate(line.rstrip('\n')):
                width = max(x + 1, width)

                p = Point(x, y)

                if c == '#':
                    walls.add(p)

                elif c.isalpha():
                    amphipods.setdefault(c, set())
                    amphipods[c].add(p)

        return State(
            width,
            height,
            frozenset(walls),
            frozendict({
                c: frozenset(points)
                for c, points in amphipods.items()
            })
        )

    def __getitem__(self, p: Union[Tuple[int, int], Point]):
        if isinstance(p, tuple):
            x, y = p
            p = Point(x, y)

        if p in self.walls:
            return '#'

        for c, points in self.amphipods.items():
            if p in points:
                return c

        return ' '

    def __str__(self):
        map_data = []

        for y in range(self.height):
            for x in range(self.width):
                map_data.append(self[x, y])
            map_data.append('\n')

        return f'State<{self.width}x{self.height}>{{\n{"".join(map_data)}}}'
```

I'm eventually going to use A* again, so in order to do that, I have to make sure everything is immutable and can be hashed, thus the `frozenset` and `frozendict` everywhere. I wish that were more elegant. 

Next up, we want the ability to generate a list of moves from a given state. That is, check every amphipod and generate every move they could make following the three rules:

```python
@dataclass(frozen=True)
class State:
    ...

    def moves(self) -> Generator[Tuple[int, 'State'], None, None]:
        '''Generate the possible next states that we can get into from here.'''

        logging.debug('Generating moves')

        for c, points in self.amphipods.items():
            logging.debug(f'- Generating moves for {c=}')

            for p in points:
                logging.debug(f'-- Generating moves for {c=} @ {p=}')

                # Move amphipods from rooms to the hallway
                # Blocked amphipods won't floodfill, so this is fine
                if p.y >= 2:
                    logging.debug('-- Dealing with a room amphipod')
                    for new_p in self.floodfill(p):
                        # An amphipod will always stop in the hallway
                        if new_p.y != 1:
                            continue

                        # ORIGINAL (WRONG) CONDITION:
                        # # An amphipod will not stop immediately outside of the room they came from
                        # if new_p.x == p.x:
                        #    continue

                        # An amphipod will not stop immediately outside of any room
                        if new_p.x in TARGET_ROOMS.values():
                            continue

                        # Otherwise, yield this as a possibility
                        yield (p.distance(new_p) * ENERGY_COSTS[c], self.move(p, new_p))

                # An amphipod in the hallway will only go into a room
                # + only it's correct room
                # + only if there are no non-similar amphipods beneath it
                elif p.y == 1:
                    logging.debug('-- Dealing with a hallway amphipod')
                    for new_p in self.floodfill(p):
                        # An amphipod will not stay in the hallway once they are in it
                        if new_p.y == 1:
                            continue

                        # An amphipod will only got into it's own room
                        if new_p.x != TARGET_ROOMS[c]:
                            continue

                        # An amphipod will not enter a room that has other kinds of amphipods in it
                        if new_p.y >= 2 and any(
                                self[new_p.x, y] not in (c, ' ')
                                for y in range(2, self.height - 1)
                        ):
                            continue

                        # Otherwise, yield this as a possibility
                        yield (p.distance(new_p) * ENERGY_COSTS[c], self.move(p, new_p))

                # This shouldn't happen...
                else:
                    logging.critical(f'Confused amphipod: {c} @ {p}')
```

That's the simulation in a nutshell, although we do need a two helper functions of course:

```python
class State:
    ...
    
    def floodfill(self, origin: Point) -> Generator[Point, None, None]:
        '''Generate all points reachable from a given location.'''

        scanned = set()
        to_scan = queue.Queue()
        to_scan.put(origin)

        while not to_scan.empty():
            p = to_scan.get_nowait()

            if p in scanned:
                continue

            scanned.add(p)

            if p != origin:
                yield p

            for xd, yd in NEIGHBORS:
                new_p = Point(p.x + xd, p.y + yd)

                if self[new_p] == ' ':
                    to_scan.put(new_p)

    def move(self, src: Point, dst: Point) -> 'State':
        '''Return a new state with the given amphipod moved from src to dst'''

        for delta_c, points in self.amphipods.items():
            if src in points:
                break

        return State(
            self.width,
            self.height,
            self.walls,
            frozendict({
                c: points if c != delta_c else points - {src} | {dst}
                for c, points in self.amphipods.items()
            })
        )
```

It's all immutable, so generate a new state for `move` and scan only empty spaces for `floodfill`. As seen in `moves`, we deal with the actual rules there, `floodfill` just needs to generate spaces that are connected and empty. 

So that's all we have:

```python
@app.command()
def main(initial_file: typer.FileText, goal_file: typer.FileText):
    initial = State.read(initial_file)
    goal = State.read(goal_file)

    q = queue.PriorityQueue()
    q.put((0, initial))

    visited = set()

    i = 0
    while not q.empty():
        energy, state = q.get_nowait()

        i += 1
        if i % 10000 == 0:
            logging.info(
                f'[{i=}, qsize={q.qsize()}] '
                f'{energy=} {str(state)}'
            )

        if state in visited:
            continue
        else:
            visited.add(state)

        if state == goal:
            break

        for new_energy, new_state in state.moves():
            q.put((energy + new_energy, new_state))

    print('Final solution:')
    print(state)
    print('states examined:', i)
    print(energy)
```

For now, all we're doing is sorting states by energy expended and trying all states until we find one that works. And it works pretty well:

```bash
$ python3 amphipodinator.py main input1.txt goal1.txt

Final solution:
State<13x5>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #########
}
states examined: 896123
11608
# time 99305909917ns / 99.31s
```

But... I feel like we can do better. Remember how I mentioned A*? Let's write a heuristic function:

```python
class State:
    ...

    def heuristic(self) -> int:
        '''Guess how many movies it will take to get to the final state.'''

        # For any amphis not in the target room, calculate a guess cost to get there
        # This will go to the hallway and into their room ignoring everything in their way
        return sum(
            (
                p.y - 1                       # To the hallway, 0 if in hallway already
                + abs(p.x - TARGET_ROOMS[c])  # Along the hallway the quickest way
                + 1                           # Into the room (first spot, underestimates)
            ) * ENERGY_COSTS[c]
            for c, points in self.amphipods.items()
            for p in points
            if p.x != TARGET_ROOMS[c]
        )
```

Because the amphipods can just run right through one another, this will never overestimate (which is required to guarantee an optimal solution from A*), but it should help. Add it to the solver:

```python
@app.command()
def main(initial_file: typer.FileText, goal_file: typer.FileText, heuristic: bool = False):
    initial = State.read(initial_file)
    goal = State.read(goal_file)

    q = queue.PriorityQueue()
    q.put((0, 0, initial))

    visited = set()

    i = 0
    while not q.empty():
        heuristic_score, energy, state = q.get_nowait()

        i += 1
        if i % 10000 == 0:
            logging.info(
                f'[{i=}, qsize={q.qsize()}] '
                f'heuristic={heuristic_score if heuristic else "disabled"} '
                f'{energy=} {str(state)}'
            )

        if state in visited:
            continue
        else:
            visited.add(state)

        if state == goal:
            break

        for new_energy, new_state in state.moves():
            if heuristic:
                heuristic_score = energy + new_energy + new_state.heuristic()
            else:
                heuristic_score = 0

            q.put((heuristic_score, energy + new_energy, new_state))

    print('Final solution:')
    print(state)
    print('states examined:', i)
    print(energy)
```

I like how the state doesn't care at all, it's all in the wrapping algorithm that uses it. So run it:

```bash
$ python3 amphipodinator.py --heuristic main input1.txt goal1.txt
Final solution:
State<13x5>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #########
}
states examined: 156876
11608
# time 18045001792ns / 18.05s
```

Nice! It examined 150k versus 900k states (6x fewer) and ran 5x as fast! That will help with part 2 I'm sure. :D

#### **Part 2:** Add two more (given) amphipods to each room, solve for least energy.

Yup, it's just bigger and more complicated. Nothing else changes:

```python
$ python3 amphipodinator.py --heuristic main input2.txt goal2.txt
Final solution:
State<13x7>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #A#B#C#D#
  #A#B#C#D#
  #########
}
states examined: 784637
46754
# time 158144712250ns / 158.14s
```

Nice! And it only had just shy of 800k states total. I know without the heuristic it would have been... somewhat more than that. 

One interesting note. I originally read the rules differently. I thought that:

* amphipods would go as deep into their room as possible and stay there (this is wrong, they can go into their room *and come back out* if that's more efficient)
* amphipods could stop in front of each other's rooms, just not their own

In both cases, I still got an answer, it just wasn't as efficient as the problem wanted. Turns out it's better for A to be able to go in and out of their room to get out of the rest's ways. It didn't matter in part 1 (other than making it a hair quicker), but it did for part 2!

A neat problem. I like how relatively elegant the rules can be expressed. 