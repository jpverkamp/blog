---
title: "AoC 2024 Day 25: Christmas Lockpickinator"
date: 2024-12-25 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 25: Code Chronicle](https://adventofcode.com/2024/day/25)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day25.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are given a series of locks and keys (see below). How many unique `(lock, key)` are there that do not overlap (they do not have to fit perfectly). 
>
> A lock starts from the top. The entire top row is `#` and the entire bottom row is `.`. 
>
> ```text
> #####
> .####
> .####
> .####
> .#.#.
> .#...
> .....
> ```
>
> A key is the opposite:
>
> ```text
> .....
> .....
> .....
> #....
> #.#..
> #.#.#
> #####
> ```

<!--more-->

Like the last day of Advent of Code generally is, it's a lighter day. Most of the weirdness in this day comes from parsing:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum LocksAndKeys {
    Lock([u8; 5]),
    Key([u8; 5]),
}

#[aoc_generator(day25)]
fn parse(input: &str) -> Vec<LocksAndKeys> {
    let mut lines = input.lines();
    let mut result = vec![];

    loop {
        let mut buffer = vec![];
        for _ in 0..7 {
            let line = lines.next().unwrap();
            buffer.push(line);
        }

        let is_lock = buffer[0].starts_with('#');
        let mut values = [0u8; 5];

        // First and last line are always ### and ...
        // For locks, it's #s going down, otherwise . going up
        #[allow(clippy::needless_range_loop)]
        for x in 0..5 {
            values[x] = if is_lock {
                (0..5)
                    .find(|y| buffer[y + 1].chars().nth(x).unwrap() == '.')
                    .unwrap_or(5)
            } else {
                (0..5)
                    .find(|y| buffer[5 - y].chars().nth(x).unwrap() == '.')
                    .unwrap_or(5)
            } as u8;
        }

        result.push(if is_lock {
            LocksAndKeys::Lock(values)
        } else {
            LocksAndKeys::Key(values)
        });

        if lines.next().is_none() {
            break;
        }
    }

    result
}
```

I totally could have done that much easier by iterating over each row and adding to the `values` rather than setting each value once. So it goes. 

And the problem:

```rust
#[aoc(day25, part1, v1)]
fn part1_v1(input: &[LocksAndKeys]) -> usize {
    use LocksAndKeys::*;

    input
        .iter()
        .permutations(2)
        .filter(|p| {
            let a = p[0];
            let b = p[1];

            // We'll generate both orders, so only count the one with the lock first
            // A lock and key match if there's no overlap *not* if they're exact
            match (a, b) {
                (Lock(a), Key(b)) => a.iter().zip(b.iter()).all(|(a, b)| a + b <= 5),
                _ => false,
            }
        })
        .count()
}
```

Runtime:

```bash
$ cargo aoc --day 25

AOC 2024
Day 25 - Part 1 - v1 : 2835
	generator: 343.708µs,
	runner: 16.44375ms
```

I could probably get that sub-millisecond, but it's Christmas. This is enough for now. :smile: 

## Part 2

> There's never a part 2 on day 25 :smile:

Merry Christmas! 

## Benchmarks

```bash
$ cargo aoc bench --day 25

Day25 - Part1/v1        time:   [5.3849 ms 5.4248 ms 5.4770 ms]
```