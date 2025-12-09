---
title: "AoC 2025 Day 7: Laser Splittinator"
date: 2025-12-07 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 7: Laboratories](https://adventofcode.com/2025/day/7)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day7.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are given a map like this:
>
> ```text
> .......S.......
> ...............
> .......^.......
> ...............
> ......^.^......
> ...............
> ```
> 
> A laser shines from the top `S` and splits each time it hits a `^`, making this:
>
> ```text
> .......S.......
> .......|.......
> ......|^|......
> ......|.|......
> .....|^|^|.....
> .....|.|.|.....
> ```
>
> The two lasers in the center of this example merge to count as one laser.
>
> Count how many times lasers hit splitters. 

<!--more-->

Okay, plan of attack today will be to create a [[wiki:bitmask]]() running across the row initialized so that only `S` is `true`. Then for each row:

* cells that are empty will have whatever value the cell above them did (lasers shining straight down)
* splitters will light up the cells on either side and not themselves (+ count these)

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
enum Tile {
    Start,
    Split,
    Empty,
}

#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let splitter_grid = Grid::read(input, |c| match c {
        'S' => Tile::Start,
        '^' => Tile::Split,
        '.' => Tile::Empty,
        _ => unreachable!("Unknown character {c:?}"),
    });

    let splitter_x = splitter_grid
        .iter()
        .find_map(|(x, _, t)| if t == Tile::Start { Some(x) } else { None })
        .unwrap();

    let mut lasers = vec![false; splitter_grid.width() as usize];
    lasers[splitter_x as usize] = true;

    let mut buffer = vec![false; splitter_grid.width() as usize];
    let mut split_count = 0;

    for y in 1..splitter_grid.height() {
        buffer.fill(false);

        for x in 0..splitter_grid.width() {
            let idx = x as usize;
            if !lasers[idx] {
                continue;
            }

            match splitter_grid.get(x, y).unwrap() {
                Tile::Start | Tile::Empty => {
                    buffer[idx] = lasers[idx];
                }
                Tile::Split => {
                    split_count += 1;

                    if x > 0 {
                        buffer[idx - 1] = true;
                    }
                    if x < splitter_grid.width() - 1 {
                        buffer[idx + 1] = true;
                    }
                }
            }
        }

        std::mem::swap(&mut lasers, &mut buffer);
    }

    split_count.to_string()
}
```

I did it with a [[wiki:double buffer]](), swapping on each iteration, rather than making new `vec` all the way down.

```bash
$ just run-and-bench 7 part1

1613

part1: 54.752µs ± 5.571µs [min: 48.416µs, max: 84.917µs, median: 52.5µs]
```

Good enough for me!

## Part 2

> Now, each time a laser hits a splitter, assume all of reality splits into two [[wiki:mirror universes]](), one where the laser went left and one where it went right. How many total universes are generated? 

We could just simulate it, but I expect the number of universes will be ... large. So instead, let's [[wiki:dynamic program]]() it. Create the same `vec` across rows as before, but this time each cell will represent how many ways a laser could have gotten to that point. 

So now:

* an empty cells gets whatever value was directly above it (+ any splitters below)
* a splitter adds the value above it to the left and right cells

Then at the end, we should be able to just sum the last counts:

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let splitter_grid = Grid::read(input, |c| match c {
        'S' => Tile::Start,
        '^' => Tile::Split,
        '.' => Tile::Empty,
        _ => unreachable!("Unknown character {c:?}"),
    });

    let splitter_x = splitter_grid
        .iter()
        .find_map(|(x, _, t)| if t == Tile::Start { Some(x) } else { None })
        .unwrap();

    // This time, keep a count of how many ways a laser could get to this position
    let mut lasers = vec![0_usize; splitter_grid.width() as usize];
    lasers[splitter_x as usize] = 1;

    let mut buffer = vec![0_usize; splitter_grid.width() as usize];

    for y in 1..splitter_grid.height() {
        buffer.fill(0_usize);

        for x in 0..splitter_grid.width() {
            let idx = x as usize;
            if lasers[idx] == 0 {
                continue;
            }

            match splitter_grid.get(x, y).unwrap() {
                // Lasers shining down, just directly add to ways to get here
                Tile::Start | Tile::Empty => {
                    buffer[idx] += lasers[idx];
                }
                // But splitters add in both directions
                Tile::Split => {
                    if x > 0 {
                        buffer[idx - 1] += lasers[idx];
                    }
                    if x < splitter_grid.width() - 1 {
                        buffer[idx + 1] += lasers[idx];
                    }
                }
            }
        }

        std::mem::swap(&mut lasers, &mut buffer);
    }

    lasers.iter().sum::<usize>().to_string()
}
```

And...

```bash
$ just run-and-bench 7 part2

48021610271997

part2: 47.854µs ± 6.221µs [min: 43.334µs, max: 88.458µs, median: 47.208µs]
```

Voila! Turns out, yes. That is in fact quite a few parallel universes. 50 trillion of them. Fun fact: that's the same order of magnitude as how many blood cells are in the average human body!

## Benchmarks

```bash
$ just bench 7

part1: 50.033µs ± 3.791µs [min: 46.333µs, max: 61.417µs, median: 48.792µs]
part2: 45.279µs ± 3.015µs [min: 43.583µs, max: 57.083µs, median: 43.75µs]
```

It's actually kind of cool to me that part 2 is *faster*. I expect that's because there are less conditionals. Perhaps rewriting part1 with `|=`? Anyways:

| Day | Part | Solution | Benchmark          |
| --- | ---- | -------- | ------------------ |
| 7   | 1    | `part1`  | 50.033µs ± 3.791µs |
| 7   | 2    | `part2`  | 45.279µs ± 3.015µs |

## Rendering

Because I can! Part 1:

<video controls src="/embeds/2025/aoc/aoc2025_day7_part1_vid.mp4"></video>

And part 2:

<video controls src="/embeds/2025/aoc/aoc2025_day7_part2_vid.mp4"></video>