---
title: "AoC 2025 Day 5: Range Merginator"
date: 2025-12-05 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 5: Cafeteria](https://adventofcode.com/2025/day/5)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day5.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a list of ranges (inclusive) and a list of IDs, how many of the IDs are in any range? 

<!--more-->

First parsing:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct Puzzle {
    ranges: Vec<(usize, usize)>,
    ids: Vec<usize>,
}

impl From<&str> for Puzzle {
    fn from(s: &str) -> Self {
        let mut ranges = Vec::new();
        let mut ids = Vec::new();

        let mut lines = s.lines();

        for line in lines.by_ref() {
            if line.trim().is_empty() {
                break;
            }

            let (a, b) = line.split_once('-').unwrap();
            let a = a.parse().unwrap();
            let b = b.parse().unwrap();
            ranges.push((a, b));
        }

        for line in lines {
            let id: usize = line.trim().parse().unwrap();
            ids.push(id);
        }

        Puzzle { ranges, ids }
    }
}
```

And then solving:

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let puzzle = Puzzle::from(input);

    puzzle
        .ids
        .into_iter()
        .filter(|id| puzzle.ranges.iter().any(|(a, b)| id >= a && id <= b))
        .count()
        .to_string()
}
```

Woot!

```bash
$ just run 5 part1

874

$ just bench 5 part1

part1: 67.91µs ± 3.055µs [min: 66.292µs, max: 83.375µs, median: 66.458µs]
```

## Part 2

> How many total IDs (ignoring the given ones) are included in any range? Ranges may overlap. 

I feel like there's always a range merging problem. 

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let puzzle = Puzzle::from(input);

    let mut ranges = puzzle.ranges.clone();

    // Merge overlapping and included ranges until nothing more can be merged
    'main: loop {
        for i in 0..ranges.len() {
            for j in (i + 1)..ranges.len() {
                let (a1, b1) = ranges[i];
                let (a2, b2) = ranges[j];

                // Completely included
                if a1 >= a2 && b1 <= b2 {
                    ranges.remove(i);
                    continue 'main;
                }

                if a2 >= a1 && b2 <= b1 {
                    ranges.remove(j);
                    continue 'main;
                }

                // Overlapping
                if a1 <= b2 && a2 <= b1 {
                    let new_range = (a1.min(a2), b1.max(b2));
                    ranges[i] = new_range;
                    ranges.remove(j);
                    continue 'main;
                }
            }
        }

        break;
    }

    ranges
        .into_iter()
        .map(|(a, b)| b - a + 1)
        .sum::<usize>()
        .to_string()
}
```

Quick enough though:

```bash
$ just run 5 part2

348548952146313

$ just bench 5 part2

part2: 249.986µs ± 7.167µs [min: 245.375µs, max: 282.25µs, median: 247µs]
```

## Part 2 - Bruteforce

I already knew this was a bad idea just looking at the problem, but I was curious. 

```rust
#[aoc::register]
fn part2_bruteforce(input: &str) -> impl Into<String> {
    let puzzle = Puzzle::from(input);

    let min = puzzle.ranges.iter().map(|(a, _)| *a).min().unwrap();
    let max = puzzle.ranges.iter().map(|(_, b)| *b).max().unwrap();

    let start_time = std::time::Instant::now();

    (min..=max)
        .map(|id| {
            if id % 100_000_000 == 0 {
                let elapsed = start_time.elapsed().as_secs_f64();
                let rate = (id - min) as f64 / elapsed;
                let eta = (max  - id) as f64 / rate;
                
                println!("[{id}] Elapsed: {:.2} s, Rate: {:.2} ids/s, ETA: {:.2} s", elapsed, rate, eta);
            }
            id
        })
        .filter(|id| !puzzle.ranges.iter().any(|(a, b)| id >= a && id <= b))
        .count()
        .to_string()
}
```

(You can leave off the `.map` if you just want the solution.)

```bash
$ cargo run --release --bin day5 -- run part2_bruteforce input/2025/day5.txt

   Compiling aoc2025 v0.1.0 (/Users/jp/Projects/advent-of-code/2025)
    Finished `release` profile [optimized] target(s) in 0.71s
     Running `target/release/day5 bench part2_bruteforce --warmup 0 --iters 1 input/2025/day5.txt`
[3438500000000] Elapsed: 0.19 s, Rate: 21172359.13 ids/s, ETA: 26379745.07 s
[3438600000000] Elapsed: 4.90 s, Rate: 21242519.51 ids/s, ETA: 26292612.62 s
[3438700000000] Elapsed: 9.66 s, Rate: 21126606.20 ids/s, ETA: 26436865.03 s
[3438800000000] Elapsed: 14.36 s, Rate: 21174614.20 ids/s, ETA: 26376921.50 s
[3438900000000] Elapsed: 19.09 s, Rate: 21168465.06 ids/s, ETA: 26384578.90 s
...
```

Yeah... that's 43 weeks, give or take. Let's not let that run. 

## Benchmarks

```bash
$ just bench 5

part1: 69.969µs ± 2.217µs [min: 66.208µs, max: 76.084µs, median: 69.5µs]
part2: 261.825µs ± 12.143µs [min: 245.416µs, max: 297.042µs, median: 259.292µs]
```

| Day | Part | Solution           | Benchmark            |
| --- | ---- | ------------------ | -------------------- |
| 5   | 1    | `part1`            | 69.969µs ± 2.217µs   |
| 5   | 2    | `part2`            | 261.825µs ± 12.143µs |
| 5   | 2    | `part2_bruteforce` | ~43 weeks :smile:    |