---
title: "AoC 2025 Day 3: Loopinator"
date: 2025-12-03 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 3: Lobby](https://adventofcode.com/2025/day/3)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day3.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a list of numbers, for each find the two digits in the number which if concatenated make the largest. Sum these values. 
>
> For example: `811111111111119` should be `89`. 

<!--more-->

Okay. Let's do it:

```rust
#[aoc::register(day3, part1)]
fn part1(input: &str) -> impl Into<String> {
    input
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| {
            let digits = line
                .chars()
                .map(|c| ((c as u8) - b'0') as usize)
                .collect::<Vec<_>>();

            let mut max_v = 0;

            for (i, a) in digits.iter().enumerate() {
                for (j, b) in digits.iter().enumerate() {
                    if i >= j {
                        continue;
                    }

                    let v = *a * 10 + *b;
                    max_v = v.max(max_v);
                }
            }

            max_v
        })
        .sum::<usize>()
        .to_string()
}
```

So the interesting part is in the `map`. We're going to basically loop over each digits `a` and `b` at indexes `i` and `j`. But specifically, `i` has to be less than `j` (so the digits are in order). If we find a new largest value, update (`v.max(max_v)` updates only if v is larger.)

This seems... inefficient. 

```bash
$ just run 3

part1: 16927

$ just bench 3

part1: 1.317902ms ± 30.702µs [min: 1.286125ms, max: 1.384583ms, median: 1.308667ms]
```

But it runs!

## Part 2

> Instead of 2 digit numbers, find 12 digit numbers. 

All righty then. 

```rust
#[allow(dead_code)]
// #[aoc::register(day3, part2_bruteforce)]
fn part2_bruteforce(input: &str) -> impl Into<String> {
    input
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| {
            let digits = line.chars().map(|c| ((c as u8) - b'0')).collect::<Vec<_>>();
            let n = digits.len();

            let mut max_value = 0;

            for i1 in 0..n {
                for i2 in (i1 + 1)..n {
                    for i3 in (i2 + 1)..n {
                        for i4 in (i3 + 1)..n {
                            for i5 in (i4 + 1)..n {
                                for i6 in (i5 + 1)..n {
                                    for i7 in (i6 + 1)..n {
                                        for i8 in (i7 + 1)..n {
                                            for i9 in (i8 + 1)..n {
                                                for i10 in (i9 + 1)..n {
                                                    for i11 in (i10 + 1)..n {
                                                        for i12 in (i11 + 1)..n {
                                                            let value: usize = format!(
                                                                "{}{}{}{}{}{}{}{}{}{}{}{}",
                                                                digits[i1],
                                                                digits[i2],
                                                                digits[i3],
                                                                digits[i4],
                                                                digits[i5],
                                                                digits[i6],
                                                                digits[i7],
                                                                digits[i8],
                                                                digits[i9],
                                                                digits[i10],
                                                                digits[i11],
                                                                digits[i12]
                                                            )
                                                            .parse()
                                                            .unwrap();

                                                            max_value = value.max(max_value);
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            max_value
        })
        .sum::<usize>()
        .to_string()
}
```

Yup. 

That's a good idea. 

*Announcer voice* It was not a good idea. 

That's going to take pretty much forever. We can do better. 

## A recursive solution

So thinking about the problem, if we have to find a 12 digits number with the maximum value in some string, that's the same (basically) as finding the first 9 and then find the largest 11 digit number. 

```rust
// Find the maximum digit string of count digits in the given string
#[tracing::instrument(ret)]
fn max_digits(digits: &[u8], count: usize) -> Option<usize> {
    // Break early if we don't have enough digits left to solve the problem
    if count > digits.len() {
        return None;
    }

    // Base case: we don't need any more digits
    if count == 0 {
        return Some(0);
    }

    // Try each digit from 9 down to 0
    for target in (0..=9u8).rev() {
        // Find the first index of that digit
        for (index, digit) in digits.iter().enumerate() {
            if *digit != target {
                continue;
            }

            // Such that there is a recursive answer in the remaining digits
            if let Some(recur) = max_digits(&digits[index + 1..], count - 1) {
                return Some((*digit as usize) * 10_usize.pow((count as u32) - 1) + recur);
            }
        }
    }

    None
}
```

So this does something a bit weird with that `(0..=9u8).rev()`. Basically, it looks for the first 9 with a valid recursive answer and if (and only if) it doesn't find one, tries 8, etc. 

It then will see if there's a recursive answer (`if let Some(recur)`), we have an answer at this level, look further up. 

## Part 2 - Recursive

Let's try it for our part 2:

```rust
#[aoc::register(day3, part2)]
fn part2(input: &str) -> impl Into<String> {
    input
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| {
            let digits = line.chars().map(|c| ((c as u8) - b'0')).collect::<Vec<_>>();
            max_digits(&digits, 12).unwrap()
        })
        .sum::<usize>()
        .to_string()
}
```

That's (hopefully) pretty straight forward! 

And it's much faster (than basically forever):

```bash
$ just run 3 part2

167384358365132

$ just bench 3 part2

part2: 155.136µs ± 6.164µs [min: 146.834µs, max: 169.084µs, median: 158.959µs]
```

Heck. That's faster than the loops for part 1. 

## Part 1 - Recursive

So let's apply it there too! It's the same thing, just with `2` instead of `12`:

```rust
#[aoc::register(day3, part1_max_digits)]
fn part1_max_digits(input: &str) -> impl Into<String> {
    input
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| {
            tracing::info!("Working on {line:?}");
            let digits = line.chars().map(|c| ((c as u8) - b'0')).collect::<Vec<_>>();

            max_digits(&digits, 2).unwrap()
        })
        .sum::<usize>()
        .to_string()
}
```

And it runs fast:

```bash
$ just run 3 part1_max_digits

16927

$ just bench 3 part1_max_digits

part1_max_digits: 55.109µs ± 2.663µs [min: 53.333µs, max: 65.584µs, median: 53.583µs]
```

Woot! That's ~25x faster. None too shabby.

## Benchmarks

```bash
$ just bench 3

part1: 1.31203ms ± 23.678µs [min: 1.284416ms, max: 1.384709ms, median: 1.308167ms]
part1_max_digits: 54.131µs ± 2.798µs [min: 52.583µs, max: 68.875µs, median: 52.875µs]
part2: 147.712µs ± 5.738µs [min: 142.25µs, max: 166.416µs, median: 149.208µs]
```

| Day | Part | Solution           | Benchmark            |
| --- | ---- | ------------------ | -------------------- |
| 3   | 1    | `part1`            | 1.31203ms ± 23.678µs |
| 3   | 1    | `part1_max_digits` | 54.131µs ± 2.798µs   |
| 3   | 2    | `part2`            | 147.712µs ± 5.738µs  |