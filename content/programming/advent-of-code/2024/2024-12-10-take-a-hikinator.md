---
title: "AoC 2024 Day 10: Take-a-Hikinator"
date: 2024-12-10 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 10: Hoof It](https://adventofcode.com/2024/day/10)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day10.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a heightmap (`0` to `9`), for each `0` count how many `9` you can reach on paths that only ever increase height by exactly 1 at a time. Sum these values. 

<!--more-->

We're just reading a `Grid` of heights, so that part is easy enough:

```rust
#[aoc_generator(day10)]
fn parse(input: &str) -> Grid<u8> {
    Grid::read(input, &|c| c.to_digit(10).unwrap() as u8)
}
```

First thought to solve this: 

* For each `0`:
  * Perform a [[wiki:depth first search]]() to all `9s`

```rust
#[aoc(day10, part1, search)]
fn part1_search(input: &Grid<u8>) -> u32 {
    input
        .iter_enumerate()
        .filter(|(_, &v)| v == 0)
        .map(|(p, _)| {
            // For each 0, search for how man 9s are reachable
            let mut checked = Grid::new(input.width, input.height);
            let mut queue = vec![p];
            let mut nines_reached = 0;

            while let Some(p) = queue.pop() {
                if input.get(p) == Some(&9) {
                    nines_reached += 1;
                    continue; // no points higher than 9
                }

                p.neighbors()
                    .iter()
                    .filter(|&p2| {
                        input.in_bounds(*p2)
                            && input.get(p).unwrap() + 1 == *input.get(*p2).unwrap()
                    })
                    .for_each(|p2| {
                        if !checked.get(*p2).unwrap_or(&false) {
                            checked.set(*p2, true);
                            queue.push(*p2);
                        }
                    });
            }

            nines_reached
        })
        .sum()
}
```

That's fairly elegant code if I do say so myself. On the outer level, we'll `filter` for only the `0`s, then the `map` contains the search. 

This is plenty for this test and relatively fast:

```bash
$ cargo aoc --day 10 --part 1

AOC 2024
Day 10 - Part 1 - dynamic : 659
	generator: 20.5µs,
	runner: 340.208µs

Day 10 - Part 1 - dynamic_tupled : 659
	generator: 6.75µs,
	runner: 73.042µs
```

If you want to watch it go, I did make a nice little rendering of it:

<video controls src="/embeds/2024/aoc/day10-part1-search.mp4"></video>

The dark red points are the paths as we scan outwards from each point with the `9s` highlighted in brighter red. 

### Optimization 1: Using dynamic programming

Okay, I think that we can do a bit better than this. The realization comes partly from [part 2](#part-2), but also from looking at that pretty picture and realizing: there may be paths from multiple `0` that join together at any point up their hike before getting to a `9`; possibly splitting off. We're duplicating all that effort!

So instead, let's try a solution that uses [[wiki:dynamic programming]]():

* Initialize each `9` with a `Set` containing itself
* For `8` down to `0`:
  * For each point of this height, find all neighbors one higher than ourselves; store the union of each of those sets

Because of the `Set`, this means that if you can reach the same `9` two different ways, it will only be counted once. When you get down to `0`, each one will have a `Set` of the `9` reachable by it, so some the counts of those. 

But... I don't *really* need to use a `Set` (since we've already seen that hashing can be surprisingly expensive). Instead, let's make a `bitmap` where each `9` has a unique bit set. The problem with this... is that we have more than 128 `9s` in the puzzle (I expect this is intentional). 

Originally, I used the `bitvec` crate to solve this, but on looking, it appears that we have ~230 `9s` in our puzzle, so let's store the state as `(u128, u128)` (and explicitly fall back to the search above if our puzzle input so happens to have more than 256 entries):

```rust
#[aoc(day10, part1, dynamic_tupled)]
fn part1_dynamic_tupled(input: &Grid<u8>) -> usize {
    let mut trail_counts: Grid<(u128, u128)> = Grid::new(input.width, input.height);

    // Flag each 9 with a unique bit
    let mut index = 0;
    input.iter_enumerate().for_each(|(p, &v)| {
        if v == 9 {
            trail_counts.set(
                p,
                if index < 128 {
                    (1 << index, 0)
                } else {
                    (0, 1 << (index - 128))
                },
            );
            index += 1;
        }
    });

    // Failsafe just in case we have more than 256 nines
    if index > 256 {
        return part1_search(input) as usize;
    }

    // For each height, we're going to OR the bits of reachable 9s together
    for height in (0..=8).rev() {
        input.iter_enumerate().for_each(|(p, &v)| {
            if v == height {
                trail_counts.set(
                    p,
                    p.neighbors()
                        .iter()
                        .filter(|&p2| input.get(*p2).is_some_and(|&v| v == height + 1))
                        .map(|&p2| *trail_counts.get(p2).unwrap())
                        .reduce(|(a1, a2), (b1, b2)| (a1 | b1, a2 | b2))
                        .unwrap_or((0, 0)),
                );
            }
        });
    }

    // Sum the ratings of the 9s
    input
        .iter_enumerate()
        .filter(|(_, &v)| v == 0)
        .map(|(p, _)| {
            let &(a, b) = trail_counts.get(p).unwrap();
            a.count_ones() as usize + b.count_ones() as usize
        })
        .sum::<usize>()
}
```

Because we have the tuple, we do end up with this wacky line:

```rust
.reduce(|(a1, a2), (b1, b2)| (a1 | b1, a2 | b2))
```

But I think it still works out well enough. 

And it is faster!

```bash
$ cargo aoc --day 10 --part 1

AOC 2024
Day 10 - Part 1 - search : 659
	generator: 7.958µs,
	runner: 111.917µs

Day 10 - Part 1 - dynamic : 659
	generator: 20.5µs,
	runner: 340.208µs

Day 10 - Part 1 - dynamic_tupled : 659
	generator: 6.75µs,
	runner: 73.042µs
```

Almost 2x speedup. The `dynamic` version in the middle there is the `bitvec` solution. 

If you'd like to see roughly how this solution works:

<video controls src="/embeds/2024/aoc/day10-part1-dynamic.mp4"></video>

The red for each pixel is how many `9s` you can reach, getting brighter as you collect more of them.

Just to show a bit more dramatically how much faster the dynamic algorithm can be, here are both videos side by side:

<video controls src="/embeds/2024/aoc/day10-part1.mp4" width="100%"></video>

It's not a perfect comparison, since the amount of actual work done per frame isn't *exactly* the same, but it's pretty close. 

### Optimization 2: Smarter bitmasks

I realized after writing most of this up but before publishing it: We don't actually *need* globally unique bitmasks! Because each `9` can only be reached by a `0` at most `8` tiles away from it, we can store them all in a `u128`:

```rust
#[aoc(day10, part1, dynamic_smart)]
fn part1_dynamic_smart(input: &Grid<u8>) -> usize {
    let mut trail_counts: Grid<u128> = Grid::new(input.width, input.height);

    // Flag each 9 with a unique bit
    // The bits only have to be unique within 10 tiles of each other
    // So within a 10x10 area, assign to that bit
    input.iter_enumerate().for_each(|(p, &v)| {
        if v == 9 {
            let mask = 1u128 << ((p.x % 10) + (p.y % 10) * 10);
            trail_counts.set(p, mask);
        }
    });

    ...
}
```

Originally, I was only using an `8x8` area (thus a `u64`), but that doesn't *quite* work, since it's possible for two `9s` that are right on the edges of that to get the same ID and thus get missed. Out of 659, this missed 2. 

But... does it actually perform any better? 

```bash 
$ cargo aoc --day 10 --part 1

AOC 2024
Day 10 - Part 1 - dynamic_tupled : 659
	generator: 7.166µs,
	runner: 80.084µs

Day 10 - Part 1 - dynamic_smart : 659
	generator: 7.666µs,
	runner: 77.709µs
```

Barely. 

I think it's worth it when comparing complexity though. The mask generation is a bit more complicated, but the algorithm itself is cleaner. (the reduce is just `.reduce(|a, b| a | b)`). 

## Part 2

> Instead of counting reachable `9s`, count how many *unique* paths there are to any `9`. 

This actually ends up being a lot easier to do with dynamic programming:

```rust
#[aoc(day10, part2, dynamic)]
fn part2_dynamic(input: &Grid<u8>) -> u32 {
    let mut ratings = Grid::new(input.width, input.height);

    // All 9s can be reached one way
    input.iter_enumerate().for_each(|(p, &v)| {
        if v == 9 {
            ratings.set(p, 1);
        }
    });

    // For each height, we're going to sum the ratings of all points one higher
    for height in (0..=8).rev() {
        input.iter_enumerate().for_each(|(p, &v)| {
            if v == height {
                ratings.set(
                    p,
                    p.neighbors()
                        .iter()
                        .filter(|&p2| input.get(*p2).is_some_and(|&v| v == height + 1))
                        .map(|p2| ratings.get(*p2).unwrap_or(&0))
                        .sum(),
                );
            }
        });
    }

    // Sum the ratings of the 0s
    input
        .iter_enumerate()
        .filter(|(_, &v)| v == 0)
        .map(|(p, _)| ratings.get(p).unwrap())
        .sum()
}
```

This time, we're going to start at the `9s` and initialize that we can get to each one `1` way. Then as we go from `8` to `1` the same way, we just have to add the neighboring values together. This represents 'how many ways can we get to any different 9 via each neighbor'. 

The video for this one ends up mostly the same as what I did for [part 1](#optimization-1-using-dynamic-programming):

<video controls src="/embeds/2024/aoc/day10-part2.mp4"></video>

Colorscale changed entirely to be confusing :smile:. Red is lower, blue is higher. 

## Benchmarks

```bash
$ cargo aoc bench --day 10

Day10 - Part1/search            time:   [65.198 µs 66.052 µs 67.339 µs]
Day10 - Part1/dynamic           time:   [278.43 µs 280.80 µs 283.53 µs]
Day10 - Part1/dynamic_tupled    time:   [42.502 µs 43.356 µs 44.197 µs]
Day10 - Part1/dynamic_smart     time:   [41.415 µs 42.406 µs 43.625 µs]

Day10 - Part2/dynamic           time:   [34.976 µs 36.044 µs 37.158 µs]
```

Part 2 faster than part 1. Funny. Although it makes sense, we don't have to deal with the mask generation and `+` should be as fast as `|` (might even be faster, since you potentially don't have to deal with all of the bits?). 