---
title: "AoC 2022 Day 23: Elf Scattinator"
date: 2022-12-23 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Algorithms
- Backtracking
- Visualization
- Cellular Automata
---
## Source: [Unstable Diffusion](https://adventofcode.com/2022/day/23)

## Part 1

> Implement a [[wiki:cellular automaton]]() with the following rules:

* If you have no neighbors, don't move (*important, I forgot this one for a while*)
* Otherwise: 
  * Calculate a potential move:
    * If you have no neighbors to the north, move north
    * If not, check likewise for south, then west, than east
  * If no other agent is moving to the same space, move to your potential move
  * Otherwise, don't move
* On each frame, rotate the order the directions are checked in (`NSWE`, `SWEN`, `WENS`, `ENSW`, `NSWE`, ...)

<!--more-->

1. I love the title. [Stable Diffusion](https://huggingface.co/spaces/stabilityai/stable-diffusion), yo. 
2. Scattinator is kind of a crappy title... :smile:

In any case, first: simple parsing:

```rust
#[derive(Clone, Debug)]
struct Elves {
    locations: HashMap<Point, usize>,
}

impl From<&Path> for Elves {
    fn from(filename: &Path) -> Self {
        let mut points = HashMap::new();

        for (y, line) in iter_lines(filename).enumerate() {
            for (x, c) in line.chars().enumerate() {
                if c == '#' {
                    points.insert(Point::new(x as isize, y as isize), 0);
                }
            }
        }

        Elves { locations: points }
    }
}
```

I'm not sure why I haven't implemented `From<&Path>` before. It makes sense. 

I'm keeping track of the location (`Point`) and an age (`usize`). This isn't needed at all for the problem, but I'm going to use it for rendering later. 

To handle rotating the `Directions`, movement in a `Direction`, and where to `check` for a `Direction` (I expect you can guess):

```rust
#[derive(Copy, Clone, Debug)]
enum Direction {
    North,
    South,
    West,
    East,
}

impl Direction {
    fn proposal(round: usize, check: usize) -> Self {
        match (round + check) % 4 {
            0 => Direction::North,
            1 => Direction::South,
            2 => Direction::West,
            3 => Direction::East,
            _ => panic!("something weird happened"),
        }
    }

    fn delta(self) -> Point {
        match self {
            Direction::North => Point::new(0, -1),
            Direction::South => Point::new(0, 1),
            Direction::West => Point::new(-1, 0),
            Direction::East => Point::new(1, 0),
        }
    }

    fn check(self) -> [Point; 3] {
        match self {
            Direction::North => [Point::new(-1, -1), Point::new(0, -1), Point::new(1, -1)],
            Direction::South => [Point::new(-1, 1), Point::new(0, 1), Point::new(1, 1)],
            Direction::West => [Point::new(-1, -1), Point::new(-1, 0), Point::new(-1, 1)],
            Direction::East => [Point::new(1, -1), Point::new(1, 0), Point::new(1, 1)],
        }
    }
}
```

It's a pit the `match` checker can't figure out that 0, 1, 2, 3 are the only possible cases with `% 4`, but it's not a problem to put a `_` case in. I also wish that `West` and `East` had 5 letters for some reason... :smile: 

Other than that, just implement the `step` function:

```rust
impl Elves {
    fn step(&mut self, round: usize) -> bool {
        // First, calculate an updated set of points
        let mut moves = Vec::new();

        'next_elf: for (elf, _) in self.locations.iter() {
            // If an elf doesn't have any neighbors, don't move
            // This is important, I forgot it and got really confused
            // Counts self, so neighbors will always >= 1
            let mut neighbors = 0;
            for xd in -1..=1 {
                for yd in -1..=1 {
                    if self.locations.contains_key(&(*elf + Point::new(xd, yd))) {
                        neighbors += 1;
                    }
                }
            }
            if neighbors == 1 {
                moves.push((*elf, *elf));
                continue 'next_elf;
            }

            // Try to move each direction until we find an empty on
            for check in 0..4 {
                let direction = Direction::proposal(round, check);

                // All three checks in this direction must be empty
                if direction
                    .check()
                    .iter()
                    .any(|p| self.locations.contains_key(&(*elf + *p)))
                {
                    continue;
                }

                moves.push((*elf, *elf + direction.delta()));
                continue 'next_elf;
            }

            // If we make it this far, add a self move to avoid collisions with elves that can't move
            moves.push((*elf, *elf));
        }

        // Second, remove any duplicates
        let dedup_moves = moves
            .iter()
            .filter(|(p1, p2)| !moves.iter().any(|(q1, q2)| p1 != q1 && p2 == q2))
            .collect::<Vec<_>>();

        self.locations.iter_mut().for_each(|(_, v)| *v += 1);

        // Perform the moves
        let mut changed = false;
        for (src, dst) in dedup_moves.iter() {
            if src != dst {
                self.locations.remove(src);
                self.locations.insert(*dst, 1);
                changed = true;
            }
        }

        changed
    }
}
```

Basically, implement the algorithm above. `moves` stores the source and destination point for each agent/elf, including the ones that don't move (otherwise we'll have collisions if one wants to move and the other can't). After that, `dedup` the moves (we can't just convert to a `HashSet` and back as I might in Python because of the ages, but this is just about as quick), and perform the moves. When we move, reset the `ages`, otherwise increment them by one. 

Wrap it up and off we go:

```rust
fn part1(filename: &Path) -> String {
    let mut elves = Elves::from(filename);

    for frame in 0..10 {
        elves.step(frame);
    }

    let [min_x, max_x, min_y, max_y] = elves.bounds();

    (((max_x - min_x + 1) * (max_y - min_y + 1)) as usize - elves.locations.len()).to_string()
}
```

We do need to calculate the bounds for the simulation in order to get the score we're requested:

```rust
impl Elves {
    fn bounds(&self) -> [isize; 4] {
        let mut min_x = isize::MAX;
        let mut max_x = isize::MIN;
        let mut min_y = isize::MAX;
        let mut max_y = isize::MIN;

        for (p, _) in self.locations.iter() {
            min_x = min_x.min(p.x);
            max_x = max_x.max(p.x);
            min_y = min_y.min(p.y);
            max_y = max_y.max(p.y);
        }

        [min_x, max_x, min_y, max_y]
    }
}
```

Why a `[isize; 4]` instead of `(isize, isize, isize, isize)`? I'm ... not sure. It's quicker to type? I expect they optimize to the same thing or at least something similar. 

## Part 2

> Determine how many frames pass until the simulation stabilizes (stops changing).

Because they don't move if there are no neighbors, this makes sense. So let's just implement that:

```rust
fn part2(filename: &Path) -> String {
    let mut elves = Elves::from(filename);

    let mut final_frame = 0;
    for frame in 0.. {
        let changed = elves.step(frame);
        if !changed {
            final_frame = frame + 1;
            break;
        }
    }

    final_frame.to_string()
}
```

I already returned if the `Elves` changed, so that's really it. Using that age data, we can at least make a pretty picture though:

<video controls src="/embeds/2022/aoc23-fading.mp4"></video>

Cool. 

## Performance

```bash
$ ./target/release/23-elf-scattinator 1 data/23.txt

4241
took 72.661ms

$ ./target/release/23-elf-scattinator 2 data/23.txt

1201
took 8.247633833s
```

That certainly took a bit longer. But still only a few second. Onwards!