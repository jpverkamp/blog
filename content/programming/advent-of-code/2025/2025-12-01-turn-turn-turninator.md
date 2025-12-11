---
title: "AoC 2025 Day 1: Turn Turn Turninator"
date: 2025-12-01 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: 
- Algorithms
- Simulation
- Iterators
- Functional Programming
- Performance
- Benchmarking
- Code Optimization
- Rust Iterators
- Rust Performance
---
## Source: [Day 1: Secret Entrance](https://adventofcode.com/2025/day/1)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/bin/day1.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Implement a padlock with 100 values (0-99). Run each command (`L23` to turn left by 23 places) and then output the number of times you landed on zero.

<!--more-->

First up, let's model/simulate this!

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
struct Dial {
    size: usize,
    position: usize,
    zeroes: usize,
}

impl Dial {
    fn new(size: usize, position: usize) -> Self {
        Dial {
            size,
            position,
            zeroes: 0,
        }
    }

    fn apply(&self, turn: Turn) -> Self {
        let mut new_dial = *self;

        // Turn the dial, wrapping (in both directions) as needed
        match turn.direction {
            Direction::Left => {
                new_dial.position = (new_dial.position + new_dial.size
                    - (turn.steps % new_dial.size))
                    % new_dial.size;
            }
            Direction::Right => {
                new_dial.position =
                    (new_dial.position + (turn.steps % new_dial.size)) % new_dial.size;
            }
        }

        // Record if we landed on zero
        if new_dial.position == 0 {
            new_dial.zeroes += 1;
        }
        new_dial
    }
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
enum Direction {
    Left,
    Right,
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
struct Turn {
    direction: Direction,
    steps: usize,
}

impl From<&str> for Turn {
    fn from(s: &str) -> Self {
        let (dir_char, steps_str) = s.split_at(1);
        let direction = match dir_char {
            "L" => Direction::Left,
            "R" => Direction::Right,
            _ => panic!("Invalid direction character"),
        };
        let steps: usize = steps_str
            .parse()
            .expect(&format!("Invalid number of steps in {s}"));
        Turn { direction, steps }
    }
}
```

Why yes, this is probably (definitely) overengineered. But it first the problem well. `Dial` is the dial on the padlock and `Turn` is input, which can be read from an `&str`. The simulation already tracks `zeroes`, so we can just:

```rust
#[aoc::register(day1, part1)]
fn part1(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Turn::from)
        .fold(Dial::new(100, 50), |dial, turn| dial.apply(turn))
        .zeroes
        .to_string()
}
```

Functional programming for the win!

```bash
$ just run 1 part1

1055
```

Reading down the chain, we:
- take the input
- iterate over lines
- turn each line into a `Turn`
- apply each line in turn (heh) to a default `Dial` with a `fold`
- output the resulting `zeroes`

Yatta!

## Part 2

> Count each time you *pass* zero, not just land on it. 

I could go through and do a bunch of math to check when we're passing zero and how many times... or I can just turn `R5` into `R1 R1 R1 R1 R1`. :smile:

```rust
#[aoc::register(day1, part2)]
fn part2(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Turn::from)
        // Replace each turn into multiple turns of 1 step each
        // It would be faster to calculate how many times we pass directly...
        // But that's *really* not necessary at this scale
        .flat_map(|turn| {
            std::iter::repeat(Turn {
                direction: turn.direction,
                steps: 1,
            })
            .take(turn.steps)
        })
        .fold(Dial::new(100, 50), |dial, turn| dial.apply(turn))
        .zeroes
        .to_string()
}
```

Works great:

```bash
$ just run 1 part2

6386
```

But there is some slight (possibly) inefficiency there with creating a bunch of internal maps, what if we iter within the fold instead? Is that actually better?

```rust
#[aoc::register(day1, part2_inline)]
fn part2_inline(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Turn::from)
        .fold(Dial::new(100, 50), |dial, turn| {
            (0..turn.steps).fold(dial, |d, _| {
                d.apply(Turn {
                    direction: turn.direction,
                    steps: 1,
                })
            })
        })
        .zeroes
        .to_string()
}
```

How do they compare?

```bash
~/Projects/advent-of-code/2025 jp@venus {git master}
$ just bench 1 part2

part2: 2.237187ms ± 52.313µs [min: 2.031584ms, max: 2.337917ms, median: 2.238458ms]

$ just bench 1 part2_inline

part2_inline: 1.870518ms ± 50.308µs [min: 1.711708ms, max: 1.953917ms, median: 1.877375ms]
```

Okay, so it's a slight speedup. I think I still prefer the code of the first version though!

## Benchmarks

```bash
$ just bench 1

part1: 215.243µs ± 11.937µs [min: 202.791µs, max: 316.333µs, median: 214.416µs]
part2: 2.237187ms ± 52.313µs [min: 2.031584ms, max: 2.337917ms, median: 2.238458ms]
part2_inline: 1.870518ms ± 50.308µs [min: 1.711708ms, max: 1.953917ms, median: 1.877375ms]
```

| Day | Part | Solution       | Benchmark             |
| --- | ---- | -------------- | --------------------- |
| 1   | 1    | `part1`        | 215.243µs ± 11.937µs  |
| 1   | 2    | `part2`        | 2.237187ms ± 52.313µs |
| 1   | 2    | `part2_inline` | 1.870518ms ± 50.308µs |

I fully expect I could write that to run quite a bit quicker, but... it's day 1. And I spent a while writing macros. So we're good. Onward!
