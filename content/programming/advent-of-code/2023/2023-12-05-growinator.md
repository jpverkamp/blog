---
title: "AoC 2023 Day 5: Growinator"
date: 2023-12-05 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 5: If You Give A Seed A Fertilizer](https://adventofcode.com/2023/day/5)

{{<toc>}}

## Part 1

> You are given a set of initial values (seeds) and a series of range maps (where a range of numbers `src..src+len` maps to `dst..dst+len`). Apply each range map in tur, return the lowest resulting value. 

<!--more-->

### Types

Okay, let's start with types:

```rust
#[derive(Debug, Copy, Clone, PartialEq)]
pub enum Category {
    Seed,
    Soil,
    Fertilizer,
    Water,
    Light,
    Temperature,
    Humidity,
    Location,
}

// A range mapping; defines a range from src..=(src+len) to dst..=(dst+len)
#[derive(Debug)]
pub struct RangeMap {
    pub src: u64,
    pub dst: u64,
    pub len: u64,
}

impl RangeMap {
    // If x is in the source range, map to the destination
    pub fn apply(&self, x: u64) -> Option<u64> {
        if x < self.src || x >= self.src + self.len {
            None
        } else {
            Some(self.dst + x - self.src)
        }
    }
}

#[derive(Debug)]
pub struct CategoryMap {
    pub src_cat: Category,
    pub dst_cat: Category,
    pub range_maps: Vec<RangeMap>,
}

impl CategoryMap {
    pub fn apply(&self, x: u64) -> u64 {
        self.range_maps
            .iter()
            .find_map(|range_map| range_map.apply(x))
            .unwrap_or(x)
    }
}

#[derive(Debug)]
pub struct Simulation {
    pub seeds: Vec<u64>,
    pub category_maps: Vec<CategoryMap>,
}

```

As mentioned, a `RangeMap` takes a value `x` and if it's in the range `src..src+len` (inclusive), it will map it. 

A category map combines several of these. The `Category` fields end up not particular mattering (they're always ordered in the input) but they were useful enough for debugging. The interesting thing to note here is that the `range_maps` in a `CategoryMap` are defined as non-overlapping. 

So you basically need to find which range (if any) the input value falls in and apply that map. If none do, the input is preserved. This is why `RangeMap::apply` returns `Option<u64>`. If 
So you basically need to find which range (if any) the input value falls in and apply that map. If none do, the input is preserved. This is why `RangeMap::apply` returns `Option<u64>`. The `find_map` in `CategoryMap::apply` will then automatically find the first `RangeMap` to return `Some(...)` (or use the `unwrap_or` to default). 

Finally, the `Simulation` stores the original `seed` values plus the ordered list of `CategoryMaps`. 

### Parsing 

Okay, we know how we want the data to look, so how do we get it in that form?

`nom`.

```rust
fn category(s: &str) -> IResult<&str, Category> {
    alt((
        map(tag("seed"), |_| Seed),
        map(tag("soil"), |_| Soil),
        map(tag("fertilizer"), |_| Fertilizer),
        map(tag("water"), |_| Water),
        map(tag("light"), |_| Light),
        map(tag("temperature"), |_| Temperature),
        map(tag("humidity"), |_| Humidity),
        map(tag("location"), |_| Location),
    ))(s)
}

fn range_map(s: &str) -> IResult<&str, RangeMap> {
    let (s, (dst, src, len)) = tuple((
        complete::u64,
        preceded(space0, complete::u64),
        preceded(space0, complete::u64),
    ))(s)?;
    Ok((s, RangeMap { src, dst, len }))
}

fn category_map(s: &str) -> IResult<&str, CategoryMap> {
    let (s, (src_cat, dst_cat)) = separated_pair(
        category,
        tag("-to-"),
        terminated(category, terminated(preceded(space1, tag("map:")), newline)),
    )(s)?;
    let (s, range_maps) = separated_list1(newline, range_map)(s)?;

    Ok((
        s,
        CategoryMap {
            src_cat,
            dst_cat,
            range_maps,
        },
    ))
}

pub fn simulation(s: &str) -> IResult<&str, Simulation> {
    let (s, seeds) = delimited(
        preceded(tag("seeds:"), space1),
        separated_list1(space1, complete::u64),
        many1(newline),
    )(s)?;

    let (s, range_maps) = separated_list1(many1(newline), category_map)(s)?;
    let (s, _) = many0(newline)(s)?;

    Ok((s, Simulation { seeds, range_maps }))
}
```

I enjoy `nom`. 

### Solution

Okay, so we have a `Simulation`. Should be easy to solve it? 

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, simulation) = parse::simulation(&input).unwrap();
    assert_eq!(s, "");

    let (cat, values) = simulation.category_maps.iter().fold(
        (Category::Seed, simulation.seeds),
        |(cat, values), range_map| {
            assert_eq!(cat, range_map.src_cat);
            (
                range_map.dst_cat,
                values.iter().map(|x| range_map.apply(*x)).collect(),
            )
        },
    );
    assert_eq!(cat, Category::Location);
    let result = values.iter().min().unwrap();

    println!("{result}");
    Ok(())
}
```

Not bad. And it at least verifies that the `CategoryMaps` are in the right order!

Keen eyed observers may note that I've changed my general solution to solving these problems. Now rather than a `part1` and `part2` function, I have a separate `bin` for each part. This let's me write up alternate solutions. I'll write it up (at some point!)

## Part 2

> Treat each pair of input values as a range. So if the first two inputs to part one were `79 14`, now you have `79..=79+14`. 

### Solution 1: Brute Force

Okay, so the obvious(ish) problem here is that we're got *way* more input to deal with. Instead of 20 input values, we not have ~billions. 

Let's try it anyways!

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, mut simulation) = parse::simulation(&input).unwrap();
    assert_eq!(s, "");

    // Replace seeds with ranges
    simulation.seeds = simulation
        .seeds
        .chunks(2)
        .flat_map(|lo_hi| (lo_hi[0]..=(lo_hi[0] + lo_hi[1])).collect::<Vec<_>>())
        .collect::<Vec<_>>();

    let (cat, values) = simulation.category_maps.iter().fold(
        (Category::Seed, simulation.seeds),
        |(cat, values), range_map| {
            assert_eq!(cat, range_map.src_cat);
            (
                range_map.dst_cat,
                values.iter().map(|x| range_map.apply(*x)).collect(),
            )
        },
    );
    assert_eq!(cat, Category::Location);
    let result = values.iter().min().unwrap();

    println!("{result}");
    Ok(())
}
```

We're literally `chunk(2)` to pull out two values at a time, generating the `Ranges`, `flat_map`ing them to values, and then running the same program. 

And it's not actually *terrible*. At least not in release mode. 

```bash
$ time just run 5 2-brute

cat data/$(printf "%02d" 5).txt | cargo run --release -p day$(printf "%02d" 5) --bin part2-brute
    Finished release [optimized] target(s) in 0.01s
     Running `target/release/part2-brute`
136096660
just run 5 2-brute  89.57s user 9.88s system 96% cpu 1:42.89 total
```

Yes. I'll explain my `Justfile` as well. But as you can see, it runs. And it's *only* a minute and a half. For brute forcing the simulation billions of times... it's not bad. 

But we can do better!

### Solution 2: Parallel Brute Force

Okay, only slightly better. Let's throw [`rayon`](https://docs.rs/rayon/latest/rayon/) at the problem. In a nutshell, it makes trivial parallelism (which we certainly have here) easy to implement.

The only change is this line:

```rust
values.par_iter().map(|x| range_map.apply(*x)).collect(),
```

And the only change in that is `.iter()` to `.par_iter()`. Rayon does the rest. 

```bash
$ time just run 5 2-brute-par

cat data/$(printf "%02d" 5).txt | cargo run --release -p day$(printf "%02d" 5) --bin part2-brute-par
    Finished release [optimized] target(s) in 0.01s
     Running `target/release/part2-brute-par`
136096660
just run 5 2-brute-par  106.71s user 15.79s system 627% cpu 19.509 total
```

That... doesn't seem right. 

```bash
date +%T && time just run 5 2-brute-par && date +%T

22:38:17

cat data/$(printf "%02d" 5).txt | cargo run --release -p day$(printf "%02d" 5) --bin part2-brute-par
    Finished release [optimized] target(s) in 0.04s
     Running `target/release/part2-brute-par`
136096660
just run 5 2-brute-par  105.90s user 15.90s system 583% cpu 20.886 total

22:38:38
```

Yeah... that isn't right at all, it's closer to 20 seconds. I expect it's summing the time across the parallel workers? Weird. 

Edit: Based on [this StackExchange answer](https://apple.stackexchange.com/questions/424131/what-does-the-time-command-do-on-zsh-mac-terminal-and-what-is-the-output-of-ch) it's actually the `zsh` (which I'm using) `time` versus the `bash` one. You can get better behavior with `TIMEFMT` or `command time`, but...

We're doing Rusty things anyways, let's install and use [hyperfine](https://crates.io/crates/hyperfine).

```bash
$ hyperfine 'just run 5 2-brute'

Benchmark 1: just run 5 2-brute
  Time (mean ± σ):     101.821 s ±  1.130 s    [User: 88.594 s, System: 9.401 s]
  Range (min … max):   100.571 s … 103.679 s    10 runs

$ hyperfine 'just run 5 2-brute-par'

Benchmark 1: just run 5 2-brute-par
  Time (mean ± σ):     20.431 s ±  0.550 s    [User: 106.872 s, System: 16.119 s]
  Range (min … max):   19.815 s … 21.537 s    10 runs
```

There we go. ~5 times faster. But we can do better!

How? 

### Solution 3: Treat the Ranges as ... Ranges

So despite how cool that `.chunks(2).flat_map(...).collect` looks, as mentioned, it's really kind of terrible, multiplying the amount of work a billion times (or so). But really, we don't have to do this. 

If, instead, we treat the ranges as ranges, there are really one a handful of cases of how the range (in a `RangeMap`) can overlap the input range:

* The entire input range is lower than the `RangeMap`
* The input range starts below but includes some of the `RangeMap`
* The input range is contained in the `RangeMap`
* The input range starts in the `RangeMap` and goes off the top end
* The input range is entirely higher than the `RangeMap`
* The input range is larger and completely contains the `RangeMap`

If you look at this a different way, there are a maximum of three sub-input ranges:

* The part below the `RangeMap`
* The part overlapping the `RangeMap`
* And the part above the `RangeMap`

When we extend this to a `CategoryMap`, the first and third cases are the case where `input` is sent to the next `RangeMap` (as before), while the middle case is the one that's actually mapped and done. 

So how does this actually turn into code?

```rust


impl RangeMap {
    // Apply over an input range
    // Returns three optional ranges:
    // 1. The portion of the original range below self's range
    // 2. The portion of the original range overlapping self's range mapped to destination
    // 3. The portion of the original range above self's range
    #[allow(clippy::type_complexity)]
    pub fn apply_range(
        &self,
        input: RangeInclusive<u64>,
    ) -> (
        Option<RangeInclusive<u64>>,
        Option<RangeInclusive<u64>>,
        Option<RangeInclusive<u64>>,
    ) {
        let (input_start, input_end) = input.clone().into_inner();
        let src_end = self.src + self.len - 1;

        let below = if input_start < self.src {
            Some(input_start..=self.src.saturating_sub(1).min(input_end))
        } else {
            None
        };

        let overlap = if input_end >= self.src && input_start <= src_end {
            let overlap_start = input_start.max(self.src);
            let overlap_end = input_end.min(src_end);
            Some((self.dst + overlap_start - self.src)..=(self.dst + overlap_end - self.src))
        } else {
            None
        };

        let above = if input_end > src_end {
            Some(src_end.saturating_add(1).max(input_start)..=input_end)
        } else {
            None
        };

        (below, overlap, above)
    }
}

impl CategoryMap {
    pub fn apply_range(&self, input: RangeInclusive<u64>) -> Vec<RangeInclusive<u64>> {
        let mut ranges = vec![input.clone()];
        let mut result = vec![];

        for range_map in self.range_maps.iter() {
            let mut unchanged = vec![];

            // Mapped ranges are ready to return
            // Anything else passes to the next range map
            for range in ranges.iter() {
                let (below, overlap, above) = range_map.apply_range(range.clone());
                if let Some(below) = below {
                    unchanged.push(below);
                }
                if let Some(overlap) = overlap {
                    result.push(overlap);
                }
                if let Some(above) = above {
                    unchanged.push(above);
                }
            }

            ranges.clear();
            ranges.append(&mut unchanged);
        }

        // Any unchanged ranges after all maps are returned
        result.append(&mut ranges);

        result
    }
}
```

I'm not going to lie, the code for this is certainly uglier. 

The magic happens in the middle of `CategoryMap::apply_range`, where the `below` and `above` lists are pushed to `unchanged` (and sent to the next `RangeMap`), but `overlap` goes straight to the `result`. 

You might think that we'd want to do some deduplication/merging of ranges here, but really, it's not that bad. With 10 or so steps, splitting a maximum of three times, we're still dealing with well *well* less than a billion entries (and most don't overlap anyways). 

The comments help a bit, but you really have to decide if performance or clarity is what you need.

To actually use these though, that's not that bad (still longer):

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, simulation) = parse::simulation(&input).unwrap();
    assert_eq!(s, "");

    // Replace seeds with ranges
    let ranges = simulation
        .seeds
        .chunks(2)
        .map(|lo_hi| lo_hi[0]..=(lo_hi[0] + lo_hi[1]))
        .collect::<Vec<_>>();

    let (cat, values) =
        simulation
            .category_maps
            .iter()
            .fold((Category::Seed, ranges), |(cat, values), range_map| {
                assert_eq!(cat, range_map.src_cat);
                (
                    range_map.dst_cat,
                    values
                        .iter()
                        .flat_map(|r| range_map.apply_range(r.clone()))
                        .collect(),
                )
            });
    assert_eq!(cat, Category::Location);

    assert_eq!(cat, Category::Location);
    let result = values
        .iter()
        .map(|r| r.clone().min().unwrap())
        .min()
        .unwrap();

    println!("{result}");
    Ok(())
}
```

As before, we replace the original seeds, but this time we keep `RangeInclusives`. Then we `fold` as before, using `apply_range` instead. 

So, does it actually speed up the code?

```bash
$ hyperfine 'just run 5 2'

Benchmark 1: just run 5 2
  Time (mean ± σ):      82.8 ms ±   4.9 ms    [User: 30.9 ms, System: 12.6 ms]
  Range (min … max):    79.0 ms … 103.6 ms    28 runs

```

Why yes. Yes it does. 

It's not microseconds. But it's awfully fast. 

## Performance

So how did all the solutions compare? 

| Solution                      | Time                 |
| ----------------------------- | -------------------- |
| Part 1                        | 82.4 ms ±   5.6 ms   |
| Part 2 (Brute Force)          | 101.821 s ±  1.130 s |
| Part 2 (Parallel Brute Force) | 20.431 s ±  0.550 s  |
| Part 2 (Ranges)               | 82.8 ms ±   4.9 ms   | 

So... we're not in the microsecond range anymore. But I think that milliseconds are still *absolutely* fine. Especially with the ~1000x speedup between Brute Force and Ranges. 

And I learned about a new fun tool (hyperfine) along the way!

I'm good with this. 

Onward!