---
title: "AoC 2024 Day 2: Safinator"
date: 2024-12-02 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 2: Red-Nosed Reports](https://adventofcode.com/2024/day/2)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day2.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Count how many given lists of numbers are `safe`:
>   1. Sorted (either ascending or descending)
>   2. *Strictly* increasing/decreasing (no duplicate values)
>   3. No increase/decrease is by more than 3

<!--more-->


Fair enough. First, we'll parse:

```rust
fn parse(input: &str) -> Vec<Vec<i32>> {
    input
        .lines()
        .map(|line| {
            line.split_ascii_whitespace()
                .map(|v| v.parse::<i32>().unwrap())
                .collect::<Vec<i32>>()
        })
        .collect()
}
```

Then define what it means to be `safe`:

```rust
// Initial version takes in a vector and checks for 'safeness'
// Must be either strictly increasing or decreasing with no difference greater than 3
fn safe(report: &[i32]) -> bool {
    (report.is_sorted() || report.iter().rev().is_sorted())
        && report
            .iter()
            .zip(report.iter().skip(1))
            .all(|(a, b)| a != b && (a - b).abs() <= 3)
}
```

I like having `is_sorted()`. And because `Vec` implemented `DoubleEndedIterator`, it's fairly cheap to have all these `Iters` floating around. 

The last trick is the `zip`, but because one is `iter()` and the other is `iter().skip(1)`, that's just a fancy way of making a 2 element [[wiki:sliding window]](). 

Okay, we have that, check if all the given lists are `safe`:

```rust
#[aoc(day2, part1, initial)]
pub fn part1_initial(input: &str) -> usize {
    let input = parse(input);
    input.iter().filter(|report| safe(report)).count()
}
```

Run it:

```bash
$ cargo aoc --day 2 --part 1

AOC 2024
Day 2 - Part 1 - initial : 432
	generator: 125ns,
	runner: 134.459µs
```

Nice!

## Part 2

> How many are `safe` if you allow skipping any one element? 

Okay, this one is actually more interesting that you'd expect to do more quickly. But first, a direct solution to it:

```rust
#[aoc(day2, part2, initial)]
pub fn part2_initial(input: &str) -> usize {
    let input = parse(input);
    input
        .iter()
        .filter(|report| {
            for n in 0..report.len() {
                let mut sub_report = (*report).clone();
                sub_report.remove(n);
                if safe(&sub_report) {
                    return true;
                }
            }
            false
        })
        .count()
}
```

Basically, for each possible element, we'll create a new `report` that removes it and then check if that's safe (bailing out as soon as we find one as a small optimization). 

And it works well enough:

```bash
$ cargo aoc --day 2 --part 2

AOC 2024
Day 2 - Part 2 - initial : 488
	generator: 42ns,
	runner: 293.333µs
```

But... despite the fact that it's already running in ~300µs (which really is plenty fast), we can do better.

## Optimization 1: Don't clone `vec`

The main problem we have is the `(*report).clone()`. The `reports` are small, but it's still a not insignificant cost to keep making more and more copies of those. 

But we don't *have* to. What if we had an `Iter` that could still iterate over that same `Vec`, but skip one element? 

Or alternatively (and this was the way I went with it), what if `safe` took an `Iterator` and then we could construct (and clone) iterators instead of the `Vec` themselves. They'll all share one `Vec` so should be much cheaper to clone. 

```rust
// Optimized version that takes in a reversible iterator and does the same
// This will allow us to skip values in the middle of the list
// And because we're only cloning the iter (not the entire vec) can be faster for part 2
fn safe_iter<'a, I>(report_iter: I) -> bool
where
    I: DoubleEndedIterator<Item = &'a i32> + Clone,
{
    (report_iter.clone().is_sorted() || report_iter.clone().rev().is_sorted())
        && report_iter
            .clone()
            .zip(report_iter.clone().skip(1))
            .all(|(a, b)| a != b && (a - b).abs() <= 3)
}
```

Okay, that's some black magic, I'll admit. There are a few things to check out:

```rust
where I: DoubleEndedIterator<Item = &'a i32> + Clone
```

All this is saying is that `safe_iter` takes any `DoubleEndedIterator` that iterates over `&i32` *that can also be cloned*. Double ended just means that it's reversible, which `Vec`'s is. 

And `clone` is... well, we're going to make several copies of the iterator, since we need to iterate at through up to 4 times (sorted, reverse sorted, and 2 for the element checks). 

How do we actually use that? 

```rust
#[aoc(day2, part1, iterator)]
pub fn part1(input: &str) -> usize {
    let input = parse(input);
    input
        .iter()
        .filter(|report| safe_iter(report.iter()))
        .count()
}

#[aoc(day2, part2, iterator)]
pub fn part2(input: &str) -> usize {
    let input = parse(input);
    input
        .iter()
        .filter(|report| {
            (0..report.len())
                .any(|n| safe_iter(report.iter().take(n).chain(report.iter().skip(n + 1))))
        })
        .count()
}
```

`part1` remains fairly straight forward. We just need to send `report.iter()` instead. The performance supports that:

```bash
$ cargo aoc --day 2 --part 1

AOC 2024
Day 2 - Part 1 - initial : 432
	generator: 125ns,
	runner: 134.459µs

Day 2 - Part 1 - iterator : 432
	generator: 83ns,
	runner: 134.042µs
```

Less than 1µs in runtime. It's actually *slightly* faster in general, although I expect it's mostly noise. 

`part2` is a bit weirder, since we want to create a new `iter` that skips an element:

```rust
report
    .iter()
    .take(n)
    .chain(report.iter().skip(n + 1))
```

I think it's clear enough, take the first `n` and then add the rest (skipping `n` and then `1` more--the only one we *actually* skip). 

Other than that, we `filter` if `any` is `safe_iter`, so we have the same early exit as before. 

In the end, we got read of one `clone()` for the `vec` and added 4 for the `iter`. Does ... it help?

```bash
$ cargo aoc --day 2 --part 2

AOC 2024
Day 2 - Part 2 - initial : 488
	generator: 42ns,
	runner: 293.333µs

Day 2 - Part 2 - iterator : 488
	generator: 42ns,
	runner: 199.5µs
```

Yup. Roughly 1/3 faster! (It varies between 1/2 and 1/3).

And I don't *think* it's actually that much less readable. Personally, I think that's the line for me. You can *certainly* get this code to run more quickly by skipping out on various overhead (for example, input values always seem to be 1-100, so we could probably speed up parsing a decent bit). But I'm okay with wicked fast and still fairly general/readable. 

To each their own!

## Benchmarks

So, how do both versions perform with a full benchmark run?

```bash
$ cargo aoc bench --day 2

Benchmarking Day2 - Part1/initial: Collecting 100 samples in estimated 5.5021 s Day2 - Part1/initial    time:   [120.51 µs 120.73 µs 120.96 µs]
                        change: [-0.0749% +0.3389% +0.7582%] (p = 0.11 > 0.05)
                        No change in performance detected.
Found 5 outliers among 100 measurements (5.00%)
  3 (3.00%) low mild
  2 (2.00%) high mild

Benchmarking Day2 - Part1/iterator: Collecting 100 samples in estimated 5.4904 sDay2 - Part1/iterator   time:   [120.35 µs 121.58 µs 123.96 µs]
                        change: [+0.4946% +1.4258% +2.7944%] (p = 0.01 < 0.05)
                        Change within noise threshold.
Found 3 outliers among 100 measurements (3.00%)
  2 (2.00%) high mild
  1 (1.00%) high severe

Benchmarking Day2 - Part2/initial: Collecting 100 samples in estimated 5.7159 s Day2 - Part2/initial    time:   [279.26 µs 279.78 µs 280.34 µs]
                        change: [+1.6753% +2.3699% +3.0701%] (p = 0.00 < 0.05)
                        Performance has regressed.
Found 3 outliers among 100 measurements (3.00%)
  1 (1.00%) low mild
  2 (2.00%) high mild

Benchmarking Day2 - Part2/iterator: Collecting 100 samples in estimated 5.8043 sDay2 - Part2/iterator   time:   [163.52 µs 164.28 µs 165.29 µs]
                        change: [-2.9062% -0.0046% +2.4325%] (p = 1.00 > 0.05)
                        No change in performance detected.
Found 10 outliers among 100 measurements (10.00%)
  3 (3.00%) high mild
  7 (7.00%) high severe
```

See? This time, `Part1/iterator` is actually slightly slower. It varies. 

But still. Pretty quick. :smile:

I'll take it. 