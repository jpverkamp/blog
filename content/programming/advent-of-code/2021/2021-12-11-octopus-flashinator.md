---
title: "AoC 2021 Day 11: Octopus Flashinator"
date: 2021-12-11 00:00:15
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Dumbo Octopus](https://adventofcode.com/2021/day/11)

#### **Part 1:** Simulate a grid of numbers such that on each tick: advance all numbers by 1, any number that increases over 9 will 'flash' and add 1 to all neighbors (recursively, but each cell can only flash once) and then reset to 0. Count the number of flashes in the first 100 ticks. 

DIRECT SIMULATION.

```python

NEIGHBORS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 0), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


@dataclass
class Cavern:
    '''Simulation for https://adventofcode.com/2021/day/11.'''

    width: int
    height: int
    data: MutableMapping[Tuple[int, int], int]

    @staticmethod
    def from_file(file: TextIO):
        '''Load a simulation from a file-like object.'''

        data = {
            (x, y): int(value)
            for x, line in enumerate(file)
            for y, value in enumerate(line.strip())
        }
        width = max(x + 1 for (x, _) in data)
        height = max(y + 1 for (_, y) in data)

        return Cavern(width, height, data)

    def step(self):
        '''Advance the simulation 1 step, return the number of flashes.'''

        flashpoint = 0

        # First advance everyone 1
        for (x, y) in self.data:
            self.data[x, y] += 1

        # Repeatedly find any 9s, but only trigger each one once (advanced)
        advanced = set()
        while True:

            # Find the set of points that haven't been advanced and should
            to_advance = {
                (x, y)
                for (x, y) in self.data
                if (x, y) not in advanced and self.data[x, y] > 9
            }

            # If we didn't, we're done
            if not to_advance:
                break

            # If we did, increment each neighbor
            for (x, y) in to_advance:
                flashpoint += 1

                for (xd, yd) in NEIGHBORS:
                    if (x + xd, y + yd) not in self.data:
                        continue

                    self.data[x + xd, y + yd] += 1

                advanced.add((x, y))

        # Once we're out of the loop, set all points that actually advanced (hit 9) to 0
        for (x, y) in advanced:
            self.data[x, y] = 0

        return flashpoint

    def __str__(self):
        return '\n'.join(
            ''.join(str(self.data[x, y]) for y in range(self.height))
            for x in range(self.width)
        ) + '\n'
```

I particularly enjoy that `step` function. It seems pretty clean to me, using one `set` of values we've already `advanced` and calculating a new `set` of values `to_advance` so that we don't duplicate. 

And it makes for pretty clean code!

```python
def part1(file: typer.FileText):

    cavern = Cavern.from_file(file)
    flashpoint = 0

    for i in range(100):
        flashpoint += cavern.step()

    print(flashpoint)
```

How many flashes?

```bash
$ python3 octopus-flashinator.py part1 input.txt
1679
```

<!--more-->

#### **Part 2:** Find the first frame where all of the points flash at the same time. 

Neat. I already have this information, since we count and return how many flashes there are each frame. We're looking for a frame when the number of flashes is equal to the number of cells (width * height):

```python
def part2(file: typer.FileText):

    cavern = Cavern.from_file(file)
    generation = 0

    while True:
        generation += 1
        flashpoint = cavern.step()

        if flashpoint == cavern.width * cavern.height:
            break

    print(generation)
```

More than 100?

```bash
$ python3 octopus-flashinator.py part2 input.txt
519
```

Of course! 

#### Animation station

Okay, this one is just begging for an animation, no?

```python
def animate(file: typer.FileText, generations: int, filename: Path):
    from PIL import Image  # type: ignore

    SCALE = 8

    cavern = Cavern.from_file(file)
    frames = []

    def add_frame():
        image = Image.new('RGB', (cavern.width, cavern.height), (0, 0, 0))
        pixels = image.load()

        for x in range(cavern.width):
            for y in range(cavern.height):
                value = int(255 * cavern.data[x, y] / 10)
                pixels[x, y] = (value, value, value)

        frames.append(image.resize((cavern.width * SCALE, cavern.height * SCALE), Image.NEAREST))

    add_frame()

    for _ in range(generations):
        cavern.step()
        add_frame()

    frames[0].save(filename, save_all=True, loop=0, duration=40, append_images=frames[1:])
```

Running it for 600 shows exactly what the problem describes: increasing synchronization eventually settling in a steady state (watch it for a bit, it loops):

{{< figure src="/embeds/2021/aoc2021-11-octopus.gif" >}}