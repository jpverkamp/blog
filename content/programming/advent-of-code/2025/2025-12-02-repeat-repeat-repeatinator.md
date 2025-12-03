---
title: "AoC 2025 Day 2: Repeat Repeat Repeatinator"
date: 2025-12-02 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 2: Gift Shop](https://adventofcode.com/2025/day/2)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day2.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a list of ranges `a-b` (ie `11-22`), sum all values that are made of two repeated chunks of digits (ie `123123`)

<!--more-->

Let's just do this the direct way:

```rust
#[aoc::register(day2, part1)]
fn part1(input: &str) -> impl Into<String> {
    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .flat_map(|(start, end)| (start..=end))
        .filter(|num| {
            let s = num.to_string();
            s[..s.len() / 2] == s[s.len() / 2..]
        })
        .sum::<usize>()
        .to_string()
}
```

So that's a quick chain of:

* Split into ranges
* Parse ranges into numbers
* `flat_map` to loop over all the numbers
* `filter` out numbers that are not duplicates (by literally making a string and comparing halves)
* Sum them

Which works well enough:

```bash
$ just run 2 part1

24157613387
```

But can we do better? 

## Part 1 - Regex

Well, for one, this seems like it would actually be perfect for a well tuned regex engine. The pattern they're describing is exactly `^(\d+)\1$` (start of string, group of digits, back reference for the same group, end of string). 

```rust
#[aoc::register(day2, part1_regex)]
fn part1_regex(input: &str) -> impl Into<String> {
    let re = fancy_regex::Regex::new(r"^(\d+)\1$").unwrap();

    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .flat_map(|(start, end)| (start..=end))
        .filter(|num| re.is_match(&num.to_string()).unwrap_or(false))
        .sum::<usize>()
        .to_string()
}
```

I started with the {{<crate regex>}}... but that one doesn't support backreferences at all. So I used {{<crate fancy_regex>}} instead. 

Which does give the right answer:

```bash
$ just run 2

part1: 24157613387
part1_regex: 24157613387
```


But the problem is:

```bash
$ just bench 2

part1: 49.40959ms ± 490.658µs [min: 48.6975ms, max: 51.310625ms, median: 49.346458ms]
part1_regex: 803.93951ms ± 10.616642ms [min: 791.386458ms, max: 858.2955ms, median: 802.344584ms]
```

It's roughly ~15x slower. 

Nope!

## Part 2 - Matching Integers

Okay, what if the actual problem is making strings. We're allocating a ton. Let's use some math instead:

```rust
#[aoc::register(day2, part1_intmatch)]
fn part1_intmatch(input: &str) -> impl Into<String> {
    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .flat_map(|(start, end)| (start..=end))
        .filter(|num| {
            let digits = (*num as f64).log10() as usize + 1;
            num / 10_usize.pow((digits / 2) as u32)
                == num % 10_usize.pow((digits / 2) as u32)
        })
        .sum::<usize>()
        .to_string()
}
```

Which:

```bash
$ just run 2 part1_intmatch

24157613387

$ just bench 2 part1_intmatch

part1_intmatch: 11.345876ms ± 110.593µs [min: 11.100958ms, max: 11.64625ms, median: 11.310459ms]
```

Which is actually ~5x faster. So that's not terrible. We still have a few expensive operations there (`log10`, `/` and `%` aren't cheap). 

You can actually do slightly faster yet:

```rust
// ...
        .filter(|num| {
            let digits = (*num as f64).log10() as usize + 1;
            let (q, r) = num.div_mod_floor(&10_usize.pow((digits / 2) as u32));
            q == r
        })
// ...
```

This requires the {{<crate num>}} crate, but it does the `div` and `mod` at the same time, rather than doing all that work twice:

```rust
$ just run 2 part1_intmatch_divrem

24157613387

$ just bench 2 part1_intmatch_divrem

part1_intmatch_divrem: 9.16757ms ± 101.928µs [min: 9.009084ms, max: 9.622834ms, median: 9.138ms]
```

## Part 2

> Sum *any* repeats of digits (with at least 2 groups), so `123123123` will now count. 

Right. Let's start with the brute force (string) solution:

```rust
#[aoc::register(day2, part2)]
fn part2(input: &str) -> impl Into<String> {
    // Test if s is made up of n repeating chunks
    fn is_repeat(s: &str, n: usize) -> bool {
        let len = s.len();
        if len % n != 0 {
            return false;
        }

        let chunk_size = len / n;
        let chunk = &s[0..chunk_size];
        for i in 0..n {
            if &s[i * chunk_size..(i + 1) * chunk_size] != chunk {
                return false;
            }
        }
        true
    }

    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .flat_map(|(start, end)| (start..=end))
        .filter(|num| {
            let s = num.to_string();
            (2..=s.len()).any(|chunk_size| is_repeat(&s, chunk_size))
        })
        .sum::<usize>()
        .to_string()
}
```

Which works fine:

```bash
$ just run 2 part2

33832678380

$ just bench 2 part2

part2: 109.286739ms ± 1.84381ms [min: 107.709334ms, max: 124.576541ms, median: 108.872875ms
```

It feels like `intmatch` on that one is going to be a bit weirder though. 

## Part 2 - Matching Integers

```rust
#[aoc::register(day2, part2_intmatch)]
fn part2_intmatch(input: &str) -> impl Into<String> {
    // Test if s is made up of n repeating chunks
    fn is_repeat(num: usize, n: usize) -> bool {
        let digits = (num as f64).log10() as usize + 1;
        if digits % n != 0 {
            return false;
        }

        let chunk_size = digits / n;
        let chunk_div = 10_usize.pow(chunk_size as u32);
        let chunk = num / chunk_div.pow((n - 1) as u32);

        for i in 0..n {
            if num / chunk_div.pow((n - 1 - i) as u32) % chunk_div != chunk {
                return false;
            }
        }
        true
    }

    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .flat_map(|(start, end)| (start..=end))
        .filter(|num| {
            let digits = (*num as f64).log10() as usize + 1;
            (2..=digits).any(|chunk_size| is_repeat(*num, chunk_size))
        })
        .sum::<usize>()
        .to_string()
}
```

Yup. That's messy. Mostly because each chunk has to do a `/` and `%`, which are both expensive. 

```bash
$ just run 2 part2_intmatch

33832678380

~/Projects/advent-of-code/2025 jp@venus {git master}
$ just bench 2 part2_intmatch

part2_intmatch: 101.440742ms ± 3.905721ms [min: 99.228ms, max: 123.911208ms, median: 100.531917ms]
```

Given that the first one was ~109ms, that really isn't *that* much faster this time. 

Still interesting to write out. 

## Benchmarks

```bash
$ just bench 2

part1: 46.189482ms ± 467.675µs [min: 45.514292ms, max: 47.419833ms, median: 46.133208ms]
part1_intmatch: 11.533401ms ± 1.266642ms [min: 11.046375ms, max: 23.946333ms, median: 11.35675ms]
part1_intmatch_divrem: 9.121032ms ± 85.661µs [min: 8.914208ms, max: 9.437417ms, median: 9.106625ms]
part1_regex: 838.820205ms ± 10.505208ms [min: 825.231ms, max: 880.588458ms, median: 835.929083ms]
part2: 110.797727ms ± 5.697853ms [min: 108.717083ms, max: 164.695708ms, median: 109.671917ms]
part2_intmatch: 100.421589ms ± 1.573153ms [min: 99.348708ms, max: 114.805125ms, median: 100.096ms]
```

| Day | Part | Solution                | Benchmark                  |
| --- | ---- | ----------------------- | -------------------------- |
| 2   | 1    | `part1`                 | 46.189482ms ± 467.675µs    |
| 2   | 1    | `part1_regex`           | 838.820205ms ± 10.505208ms |
| 2   | 1    | `part1_intmatch`        | 11.533401ms ± 1.266642ms   |
| 2   | 1    | `part1_intmatch_divrem` | 9.121032ms ± 85.661µs      |
| 2   | 1    | `part1_chatgpt`         | 650.796µs ± 231.766µs      |
| 2   | 2    | `part2`                 | 110.797727ms ± 5.697853ms  |
| 2   | 2    | `part2_intmatch`        | 100.421589ms ± 1.573153ms  |

## (Edit) Part 1 - ChatGPT

Okay. So, I know that there's a faster way to solve this, but I didn't really want to (or have the time to) go through all of the math. So I threw ChatGPT at it:

```rust
#[aoc::register(day2, part1_chatgpt)]
fn part1_chatgpt(input: &str) -> impl Into<String> {
    fn sum_repeated_halves(a: u64, b: u64) -> u128 {
        let mut total_sum: u128 = 0u128;
        let mut h = 1;

        loop {
            let low = 10u64.pow(h - 1);
            let high = 10u64.pow(h) - 1;

            let power = 10u128.pow(h);

            for x in low..=high {
                let xx = x as u128 * (power + 1);
                if xx > b as u128 {
                    break; // all larger X will exceed b
                }
                if xx >= a as u128 {
                    total_sum += xx;
                }
            }

            // stop if the smallest XX for this h exceeds b
            if low as u128 * (power + 1) > b as u128 {
                break;
            }

            h += 1;
        }

        total_sum
    }

    input
        .trim_end()
        .split(",")
        .map(|s| {
            let (a, b) = s.split_once("-").expect("Invalid range");
            (
                a.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {a}")),
                b.parse::<usize>()
                    .unwrap_or_else(|_| panic!("failed to parse {b}")),
            )
        })
        .map(|(start, end)| sum_repeated_halves(start as u64, end as u64))
        .sum::<u128>()
        .to_string()
}
```

Which:

```bash
$ just run 2 part1_chatgpt

24157613387

$ just bench 2 part1_chatgpt

part1_chatgpt: 566.21µs ± 11.597µs [min: 556.584µs, max: 608.375µs, median: 561.583µs]
```

Whelp. 

Sometimes I'm impressed as heck that GPTs work as well as they do. Especially for smaller problems (like this one), they just solve it. This took only one fix (where it was overcounting, but I showed it the code I was wrapping it with and it fixed it) and about 5 minutes. 

For larger problems? Anything where you have to actually build out a project larger goals, complex requirements, or (heaven forbid) do security right? Well, that remains to be seen. 