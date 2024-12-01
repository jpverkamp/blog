---
title: "AoC 2024 Day 1: Sortinator"
date: 2024-12-01 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 1: Historian Hysteria](https://adventofcode.com/2024/day/1)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day1.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given two lists of numbers arranged in columns in a file, find the sum of differences (in sorted order). 

<!--more-->

I'll admit, I paraphrased that a bit :smile:

Basically, we have this:

```text
3   4
4   3
2   5
1   3
3   9
3   3
```

We want to read the 'left' and 'right' columns of numbers, then find the difference between the smallest in each column, then second smallest, etc. 

Really, a lot of this problem comes down to parsing. It would be a lot easier to read them as rows. But we don't have that!

Instead:

```rust
#[aoc_generator(day1)]
fn parse(input: &str) -> (Vec<i32>, Vec<i32>) {
    input
        .lines()
        .map(|line| {
            line.split_ascii_whitespace()
                .map(|v| v.parse::<i32>().unwrap())
                .collect::<Vec<i32>>()
        })
        .map(|lss| {
            assert!(lss.len() == 2);
            (lss[0], lss[1])
        })
        .unzip()
}
```

It's ... a bit much. But essentially:

* Read the `lines()`
* For each line, `split_ascii_whitespace` and `parse` each result as an `i32`
* For each `Vec` of the above, verify it has exactly two entries and convert to a tuple
* `unzip` that, so instead of `Vec<(i32, i32)>`, we have `(Vec<i32>, Vec<i32>)`. That's a pretty cool function to have built in!

Because we have it tagged with `aoc_generator`, that means that in the `part1` / `part2` functions below, we can treat the `(Vec<i32>, Vec<i32>)` as the input type and separately benchmark parsing and running the solution!

Speaking of:

```rust
#[aoc(day1, part1, i32)]
pub fn part1(input: &(Vec<i32>, Vec<i32>)) -> i32 {
    // Unfortunate, but we do need a separate copy since we're going to sort them
    let mut ls1 = input.0.to_vec();
    let mut ls2 = input.1.to_vec();

    ls1.sort();
    ls2.sort();

    ls1.iter()
        .zip(ls2.iter())
        .map(|(v1, v2)| (v1 - v2).abs())
        .sum::<i32>()
}
```

Sort them, then `zip` the two back together. `sum` the `abs`olute difference of pairs (doesn't matter which is bigger). 

That's it!

```rust
$ cargo aoc --day 1 --part 1

AOC 2024
Day 1 - Part 1 - i32 : 2742123
	generator: 145.541µs,
	runner: 55.459µs
```

That's 1/20 of 1/1000 of 1 second. 

Pretty quick. :smile:

(And yet, in that same time light would travel 10 *miles* / 16 *km*! (In a vacuum))

## Part 2

> For each number *a* in the left list, count how many times *a* appears in the right list, multiple that count by *a*. Sum these.

```rust
#[aoc(day1, part2, i32)]
pub fn part2(input: &(Vec<i32>, Vec<i32>)) -> i32 {
    input.0.iter()
        .map(|v1| input.1.iter().filter(|v2| v1 == *v2).count() as i32 * v1)
        .sum::<i32>()
}

```

Straight forward I think. For each value, `.filter` to get only equal values and `count` (then `sum`). Should be well optimized. 

```bash
$ cargo aoc --day 1 --part 2

AOC 2024
Day 1 - Part 2 - i32 : 21328497
	generator: 215.583µs,
	runner: 123.625µs
```

## Benchmarks

```bash
$ cargo aoc bench --day 1

Day1 - Part1/i32        time:   [11.425 µs 11.542 µs 11.652 µs]
                        change: [+3.3222% +3.9587% +4.6305%] (p = 0.00 < 0.05)
                        Performance has regressed.
Found 7 outliers among 100 measurements (7.00%)
  7 (7.00%) high mild

Day1 - Part2/i32        time:   [39.095 µs 39.379 µs 39.701 µs]
                        change: [+2.4526% +2.9211% +3.4246%] (p = 0.00 < 0.05)
                        Performance has regressed.
Found 4 outliers among 100 measurements (4.00%)
  1 (1.00%) high mild
  3 (3.00%) high severe
```