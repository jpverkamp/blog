---
title: "AoC 2024 Day 8: Vectorinator"
date: 2024-12-08 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 8: Resonant Collinearity](https://adventofcode.com/2024/day/8)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day8.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a grid with either open tiles (`.`) or towers (anything else), for each pair of towers, there is an antinode at each of the points that is 2x as far from one tower as the other. How many antinodes are there still within the bounds of the map? 

<!--more-->

Parsing? Sounds `Grid`!

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum Tile {
    #[default]
    Empty,
    Tower(char),
}

#[aoc_generator(day8)]
fn parse(input: &str) -> Grid<Tile> {
    Grid::read(input, &|c| match c {
        '.' => Tile::Empty,
        _ => Tile::Tower(c),
    })
}
```

Although it turns out we don't really care about the entire grid. Just for each tower ID, we want a list of points that have that ID. 

```rust
#[aoc(day8, part1, v1)]
fn part1_v1(input: &Grid<Tile>) -> usize {
    let mut towers = hashbrown::HashMap::new();

    for (point, tile) in input.iter_enumerate() {
        if let Tile::Tower(c) = tile {
            towers.entry(c).or_insert_with(Vec::new).push(point);
        }
    }

    ...
}
```

I really could have done that in the parsing and probably didn't need to do it with a `HashMap`... but I think tha tin this case, that's really the cleanest way to do it without writing a newer parsing function and honestly, it's been a long day. That's probably enough for the moment. 

So how do we find the antinodes? Well, take each pair of towers as vectors `v1` and `v2`. The vector between them is `d = v2 - v1` and then one point will be at `v1 - d` and the other at `v2 + d`.

```rust
#[aoc(day8, part1, v1)]
fn part1_v1(input: &Grid<Tile>) -> usize {
    let mut towers = hashbrown::HashMap::new();

    for (point, tile) in input.iter_enumerate() {
        if let Tile::Tower(c) = tile {
            towers.entry(c).or_insert_with(Vec::new).push(point);
        }
    }

    let mut antinodes = Grid::new(input.width, input.height);

    for (_, points) in towers.iter() {
        for p1 in points {
            for p2 in points {
                if p1 != p2 {
                    let d = *p2 - *p1;
                    antinodes.set(*p1 - d, true);
                    antinodes.set(*p2 + d, true);
                }
            }
        }
    }

    antinodes.iter().filter(|&b| *b).count()
}
```

And that's it! 

We've saved some nice time here again by making it so that if you `set` a point out of bounds on a `Grid`, it just ignores it! Also, we get duplication removal for free (if towers with two different IDs end up having an antinode on the same point, it only counts once).

```bash
$ cargo aoc --day 8 --part 1

AOC 2024
Day 8 - Part 1 - v1 : 299
	generator: 8.75µs,
	runner: 13.75µs
```

## Part 2

> Instead of just 1 antinode in each direction, generate them in a repeating pattern:
>
> ```text
> a......
> ..a....
> ....#..
> ......#
>
> Where `a` are the towers and `#` the antinodes. 

Mostly the same code, except instead of a single point for each, we'll loop until we actually hit `in_bounds`:

```rust
#[aoc(day8, part2, v1)]
fn part2_v1(input: &Grid<Tile>) -> usize {
    let mut towers = hashbrown::HashMap::new();

    for (point, tile) in input.iter_enumerate() {
        if let Tile::Tower(c) = tile {
            towers.entry(c).or_insert_with(Vec::new).push(point);
        }
    }

    let mut antinodes = Grid::new(input.width, input.height);

    for (_, points) in towers.iter() {
        for p1 in points {
            for p2 in points {
                if p1 != p2 {
                    let delta = *p2 - *p1;

                    let mut p = *p1 + delta;
                    while input.in_bounds(p) {
                        antinodes.set(p, true);
                        p += delta;
                    }

                    let mut p = *p1 - delta;
                    while input.in_bounds(p) {
                        antinodes.set(p, true);
                        p -= delta;
                    }
                }
            }
        }
    }

    antinodes.iter().filter(|&b| *b).count()
}
```

It's probably not the *most* optimized code, but I actually think it's really clean!

```rust
cargo aoc --day 8 --part 2

AOC 2024
Day 8 - Part 2 - v1 : 1032
	generator: 8.5µs,
	runner: 18.625µs
```

I did render this one too. It's fun:

<video controls src="/embeds/2024/aoc/day8-part2.mp4" width="100%"></video>

## Benchmarks

It's been a long day, so I probably won't optimize this one too much more. We're probably paying a decent bit in parsing the `Grid` and then immediately throwing it away, plus (maybe) in keeping multiple `Vec` instead of one with offsets for each tower. So it goes. 

```bash
$ cargo aoc bench --day 8

Day8 - Part1/v1         time:   [4.4647 µs 4.5002 µs 4.5514 µs]
Day8 - Part2/v1         time:   [6.5027 µs 6.6171 µs 6.7712 µs]
```

Honestly, it's faster than [[AoC 2024 Day 7: Mathinator|yesterday]](). I'm okay with that!