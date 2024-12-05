---
title: "AoC 2024 Day 5: (Not) Transitivinator"
date: 2024-12-05 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day Day 5: Print Queue](https://adventofcode.com/2024/day/5)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day5.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> The input is a list of pairs of the form `a|b` which defines that `b` must not come before `a`, an empty line, and then a list of values `a,b,c,d`.
>
> For each line that is valid for all given `a|b` rules, sum the middle number of each list. 

<!--more-->

We'll go ahead and start with a hash of `a -> Set(b)`:

```rust
#[derive(Debug, Default, Clone)]
pub struct Ordering {
    data: hashbrown::HashMap<u32, hashbrown::HashSet<u32>>,
}

impl Ordering {
    pub fn new() -> Self {
        Self {
            data: hashbrown::HashMap::new(),
        }
    }

    pub fn insert(&mut self, a: u32, b: u32) {
        self.data.entry(a).or_default().insert(b);
    }
}
```

That lets us define `can_precede`:

```rust
impl Ordering {
    pub fn can_precede(&self, a: u32, b: u32) -> bool {
        !self.data.contains_key(&b) || !self.data[&b].contains(&a)
    }
}
```

If `b` isn't in any pair, than `a` is always fine. Otherwise, `a` can never appear in any list `b`. 

This then tells us if a given `Vec` is sorted by this `Ordering`:

```rust
impl Ordering {
    pub fn validates(&self, list: &[u32]) -> bool {
        list.iter().is_sorted_by(|&a, &b| self.can_precede(*a, *b))
    }
}
```

Which in turn basically solves the problem for us:

```rust
#[aoc(day5, part1, v1)]
fn part1_v1((ordering, data): &(Ordering, Vec<Vec<u32>>)) -> u32 {
    data.iter()
        .filter(|list| ordering.validates(list))
        .map(|list| list[list.len() / 2])
        .sum()
}
```

It's fun when most of the work is setting up abstractions.

```bash
$ cargo aoc --day 5 --part 1

AOC 2024
Day 5 - Part 1 - v1 : 4924
	generator: 119.083µs,
	runner: 19.25µs
```

Quick enough!

### Parsing

Not *super* relevant to the problem (especially since it's a fairly tame format so far as puzzle input goes), but here's my `nom` parsing function:

```rust
#[aoc_generator(day5)]
pub fn parse(input: &str) -> (Ordering, Vec<Vec<u32>>) {
    use nom::{
        character::complete::{self, newline},
        multi::{many1, separated_list1},
        sequence::separated_pair,
    };

    fn parse_ordering(input: &str) -> nom::IResult<&str, Ordering> {
        let (rest, ls) = separated_list1(
            newline,
            separated_pair(complete::u32, complete::char('|'), complete::u32),
        )(input)?;

        let mut ordering = Ordering::new();
        for (a, b) in ls {
            ordering.insert(a, b);
        }
        Ok((rest, ordering))
    }

    fn parse_list(input: &str) -> nom::IResult<&str, Vec<u32>> {
        separated_list1(complete::char(','), complete::u32)(input)
    }

    fn parse_input(input: &str) -> nom::IResult<&str, (Ordering, Vec<Vec<u32>>)> {
        let (input, ordering) = parse_ordering(input)?;
        let (input, _) = many1(newline)(input)?;
        let (input, data) = separated_list1(newline, parse_list)(input)?;
        Ok((input, (ordering, data)))
    }

    parse_input(input).unwrap().1
}
```

It actually runs about 20% faster than a `.lines()` + `.split_once('|')`, which I found interesting. And at least for me, just as easy to read if not a bit more clear.

### Is it transitive?

Second aside: one thing that really tripped me up when running this problem was the assumption that the rules in the first part would be defined such that they were [[wiki:transitive]](). So if you have:

```text
a|b
b|c
```

You can infer `a|c`. Which works perfectly well for their given example... but doesn't for our actually given test cases. It ends up you can have these rules:

```text
a|b
b|c
c|a
```

Thus forming a loop. It doesn't make any sense if you have all three `a,b,c` in an input (I guess it could just be always invalid), *but* it actually works out perfectly if you only ever include no more than two of them. `a,b` `b,c` and `c,a` are all perfectly valid to have within a given list. 

Spent more time than I wanted to track that one down:

```rust
impl Ordering {
    // This was my original (more complicated!) version, but it's not actually correct

    /*
    Imagine this input:

        98|51
        51|22
        22|98

    This would imply both that 98 is before 51 but that 51 is before 22 which is before 98.

    But... that doesn't make any sense... *unless* you can never a valid list that has all three.

    If you have 98 and 51, 98 goes first. But if you have 51,22 or 22,98 those are correct.

    I expect this would do funny things to sort_by if you end up with all three :smile:
    */

    // To proceed, either a is directly before b or recursively before it
    pub fn can_precede_transitive(&self, a: u32, b: u32) -> bool {
        self.data.contains_key(&a)
            && (self.data[&a].contains(&b) || self.data[&a].iter().any(|&c| self.can_precede(c, b)))
    }

    pub fn can_precede_transitive_path(&self, a: u32, b: u32) -> Option<Vec<u32>> {
        if !self.data.contains_key(&a) {
            return None;
        }

        if self.data[&a].contains(&b) {
            return Some(vec![a, b]);
        }

        for &c in &self.data[&a] {
            if let Some(mut path) = self.can_precede_transitive_path(c, b) {
                path.insert(0, a);
                return Some(path);
            }
        }

        None
    }
}
```

And `bin/day5-check.rs`:

```rust
use aoc2024::day5;

// Used to determine/verify that the ordering is *not* transitive
fn main() {
    let filename = std::env::args().nth(1).expect("missing filename argument");
    let content = std::fs::read_to_string(filename).expect("cannot read file");

    let (ordering, _) = day5::parse(&content);

    for a in ordering.values() {
        for b in ordering.values() {
            let proceeds = ordering.can_precede(a, b);
            let proceeds_transitive = ordering.can_precede_transitive(a, b);

            if proceeds_transitive && !proceeds {
                println!("{a} {b} {:?}", ordering.can_precede_transitive_path(a, b));
            }
        }
    }
}
```

That was how I actually verified that you can have rules that don't work transitively, but are perfectly valid for the given input. 

I'll admit, that's one of the things that both annoys me and is *such a perfect encapsulation of software development*: Occasionally ambiguous specifications. And/or specifications that are specifically written in English, but not given as concrete and comprehensive examples.

> The second and third updates are also in the correct order according to the rules. Like the first update, they also do not include every page number, and so only some of the ordering rules apply - within each update, the ordering rules that involve missing page numbers are not used.

Which does *technically* cover that edge case, but so it goes. 

Whee. :smile:

## Part 2

> For each list that is not currently valid, sort it by the given ordering and then sum the middle values. 

```rust
#[aoc(day5, part2, v1)]
fn part2_v1((ordering, data): &(Ordering, Vec<Vec<u32>>)) -> u32 {
    data.iter()
        .filter(|list| !ordering.validates(list))
        .map(|list| {
            // TODO: I don't want to have to clone this here, but AOC requires it
            let mut list = list.clone();
            list.sort_by(|&a, &b| {
                if ordering.can_precede(a, b) {
                    std::cmp::Ordering::Less
                } else {
                    std::cmp::Ordering::Greater
                }
            });
            list
        })
        .map(|list| list[list.len() / 2])
        .sum()
}
```

Nothing much to see here; we `filter` out the ones that are already sorted, `sort_by` the ones left, and `map` to the middle values. 

As mentioned, I do have one `TODO:` because of how the `cargo-aoc` crate passes input, you cannot directly mutate the input (it's always a `&T` for whatever `T` the `generator` function returns). This makes sense when it comes to benchmarking--you can't mutate the input if you're going to run the algorithm on that input 10k times. :smile:

Anyways. Still quick!

```text
cargo aoc --day 5 --part 2

AOC 2024
Day 5 - Part 2 - v1 : 6085
	generator: 124.917µs,
	runner: 207.5µs
```

Onward.

## Benchmarks

```bash
$ cargo aoc bench --day 5

Day5 - Part1/v1         time:   [8.1412 µs 8.2175 µs 8.3300 µs]
Day5 - Part2/v1         time:   [59.691 µs 60.810 µs 62.017 µs]
```

It's interesting how much faster that is than one run. Some impressive caching going on there I expect. 

## Optimization 1: Drop the `hashmap`

Okay, `hashbrown` is fast enough, but we don't *really* need that if we really want this solution to be fast. Instead, let's just throw some memory at it. We know (from looking at our input) that all values will be two digits, so let's just initialize a 100*100 array of booleans:

```rust
#[derive(Debug, Clone)]
pub struct Ordering {
    data: [bool; 100*100]
}

impl Ordering {
    pub fn new() -> Self {
        Self {
            data: [false; 100*100],
        }
    }

    pub fn insert(&mut self, a: u32, b: u32) {
        self.data[(a as usize)*100+(b as usize)] = true;
    }

    pub fn can_precede(&self, a: u32, b: u32) -> bool {
        !self.data[(a as usize)*100+(b as usize)]
    }

    pub fn validates(&self, list: &[u32]) -> bool {
        list.iter().is_sorted_by(|&a, &b| self.can_precede(*a, *b))
    }
}
```

Nothing else actually needs to change (although this can certainly `panic!` if any input is > 100). 

```bash
$ cargo aoc bench --day 5

Day5 - Part1/v1         time:   [229.10 ns 230.04 ns 231.17 ns]
Day5 - Part2/v1         time:   [14.302 µs 14.369 µs 14.437 µs]
```

That's ... nanoseconds. Whee! And a 4x speedup on part 2. 

Can we go further? 

## Optimization 2: `bitvec`

I'm not 100% sure how optimized Rust's `[bool]` is under the hood, but what if we directly use a crate that's designed to work with a `vec` of `bits`? [`bitvec`](https://docs.rs/bitvec/latest/bitvec/)!

```rust
#[derive(Debug, Clone)]
pub struct Ordering {
    data: BitVec,
}

impl Ordering {
    pub fn new() -> Self {
        Self {
            data: bitvec![0; 100*100],
        }
    }

    pub fn insert(&mut self, a: u32, b: u32) {
        self.data.set((a as usize)*100+(b as usize), true);
    }

    pub fn can_precede(&self, a: u32, b: u32) -> bool {
        !self.data[(a as usize)*100+(b as usize)]
    }

    pub fn validates(&self, list: &[u32]) -> bool {
        list.iter().is_sorted_by(|&a, &b| self.can_precede(*a, *b))
    }
}
```

Basically the same; only a few names have changed and `IndexMut` isn't defined. 

```bash
$ cargo aoc bench --day 5

Day5 - Part1/v1         time:   [304.75 ns 306.14 ns 307.66 ns]
Day5 - Part2/v1         time:   [20.223 µs 20.430 µs 20.766 µs]
```

Huh, we'll that's certainly interesting. The runtimes are a *bit* slower. It seems that the Rust folks did a pretty good job optimization `[bool]` already!

One interesting thing to note though:

```bash
# With [bool]
cargo aoc --day 5

AOC 2024
Day 5 - Part 1 - v1 : 4924
	generator: 101.291µs,
	runner: 3.292µs

Day 5 - Part 2 - v1 : 6085
	generator: 69.458µs,
	runner: 22.583µs


# With bitvec
cargo aoc --day 5

AOC 2024
Day 5 - Part 1 - v1 : 0
	generator: 83.584µs,
	runner: 1.583µs

Day 5 - Part 2 - v1 : 11009
	generator: 62.041µs,
	runner: 34.834µs
```

The `generator` part (that does the parsing and building of the initial `bitvec`) *is* ~20% faster. 

It would be interesting to dig into why exactly that is!