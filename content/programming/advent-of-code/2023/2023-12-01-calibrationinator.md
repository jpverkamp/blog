---
title: "AoC 2023 Day 1: Calibrationinator"
date: 2023-12-01 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 1: Trebuchet?!](https://adventofcode.com/2023/day/1)

## Part 1

> Given a list of alphanumeric strings, find the first and last digit on each line (they may be the same). Concatenate each pair and sum them. 

<!--more-->

We're starting out fairly light. To find the digits, we can filter out anything that is not a digit. Then concatenate, numberize, and sum. 

```rust
fn part1(filename: &Path) -> Result<String> {
    Ok(iter_lines(filename)
        .filter_map(|l| {
            let mut first = None;
            let mut last = None;

            for c in l.chars() {
                if c.is_numeric() {
                    if first.is_none() {
                        first = Some(c);
                    }
                    last = Some(c);
                }
            }

            Some(10 * first?.to_digit(10)? + last?.to_digit(10)?)
        })
        .sum::<u32>()
        .to_string())
}
```

Ironically, we're not really using the `filter_map` here. I'm only using it because if anything fails to parse, the `?` will return `None`, which we can filter out. 

Also, I'm not *that* thrilled with this answer. I'd really like to be able to filter inline, extract the first and last elements, and `product` them. Something like:

```rust
l.chars()
    .filter(|c| c.is_numeric())
    .first_and_last()
    .collect::<String>()
    .parse::<u32>()
```

But that would require a `first_and_last` function...

Okay, let's try it.

```rust
mod first_and_last {
    pub(crate) trait IteratorExt: Iterator {
        fn first_and_last(mut self) -> [Self::Item; 2]
        where
            Self: Sized,
            Self::Item: Clone,
        {
            let first = self.next().unwrap();
            let last = self.last().or_else(|| Some(first.clone())).unwrap();
            
            [first, last]
        }
    }

    impl<T: ?Sized> IteratorExt for T where T: Iterator {}

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn test_first_and_last() {
            assert_eq!(vec![1, 2, 3, 4, 5].into_iter().first_and_last(), [1, 5]);
            assert_eq!(vec![1].into_iter().first_and_last(), [1, 1]);
        }
    }
}
```

I've... no idea if this is a good idea or not. But it does simplify part 1 a bit (IMO):

```rust
fn part1(filename: &Path) -> Result<String> {
    Ok(iter_lines(filename)
        .map(|l| {
            l.chars()
                .filter(|c| c.is_numeric())
                .first_and_last()
                .iter()
                .collect::<String>()
                .parse::<u32>()
                .unwrap()
        })
        .sum::<u32>()
        .to_string())
}
```

I suppose it's up to you which you prefer!

(And this is only part 1 of day 1...)

## Part 2

> This time, treat `one`, `two`, etc as valid digits (that can be first or last). 

One thing to note here (minor spoilers): there are a few cases where numbers can overlap, such as `eightwo` being both `8` and `2`. A simple regex won't handle that. Here's how I did it: 

```rust
fn part2(filename: &Path) -> Result<String> {
    let digit_words = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    ];

    Ok(iter_lines(filename)
        .filter_map(|l| {
            let mut first = None;
            let mut last = None;

            for (i, c) in l.chars().enumerate() {
                // Match literal digits
                if c.is_numeric() {
                    let c = c.to_digit(10)? as usize;
                    if first.is_none() {
                        first = Some(c);
                    }
                    last = Some(c);
                    continue;
                }

                // Match digit words
                for (digit, word) in digit_words.iter().enumerate() {
                    if l[i..].starts_with(word) {
                        if first.is_none() {
                            first = Some(digit);
                        }
                        last = Some(digit);
                        break;
                    }
                }
            }

            Some(10 * first? + last?)
        })
        .sum::<usize>()
        .to_string())
}
```

## Performance

```bash
$ cargo run --release --bin 01-calibrationinator 1 data/01.txt

   Compiling aoc2023 v0.1.0 (/Users/jp/Projects/advent-of-code/2023)
    Finished release [optimized] target(s) in 0.19s
     Running `target/release/01-calibrationinator 1 data/01.txt`
53651
took 500.417µs

$ cargo run --release --bin 01-calibrationinator 2 data/01.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/01-calibrationinator 2 data/01.txt`
53894
took 671.791µs
```

Yeah... µs. Nothing much to bother here. 