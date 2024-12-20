---
title: "AoC 2024 Day 19: Regexinator"
date: 2024-12-19 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics: 
- Regular Expressions
- Regex
- Backtracking
- Memoization
- ReDoS 
- Regular Expression Denial of Service
---
## Source: [Day 19: Linen Layout](https://adventofcode.com/2024/day/19)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day19.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a comma delimited list of substrings and a list of strings, count how many of the latter strings can be made up of any (repeating) combination of the former. 

<!--more-->

This is a (rather simplified) subset of regular expressions. And hey, I [wrote one of those]({{<ref "CodeCrafters: Build Myself a Grep">}})! Basically, if we're doing the example input:

```text
r, wr, b, g, bwu, rb, gb, br

brwrr
bggr
gbbr
rrbgbr
ubwu
bwurrg
brgr
bbrgwb
```

We're testing how many of those strings match `^(r|wr|b|g|bwu|rb|gb|br)$`. 

Let's start by just throwing the [`regex` crate](https://docs.rs/regex/latest/regex/) at it:

```rust
#[aoc(day19, part1, regex)]
fn part1_regex(input: &str) -> usize {
    let puzzle: Puzzle = input.into();

    let regex = format!("^({})+$", &puzzle.towels.join("|"));
    let regex = Regex::new(regex.as_str()).unwrap();

    puzzle
        .targets
        .iter()
        .filter(|target| regex.is_match(target))
        .count()
}
```

Simple code, and...

```bash
$ AOC 2024
Day 19 - Part 1 - regex : 336
	generator: 125ns,
	runner: 5.632208ms
```

...fairly fast. 

### Let's write it ourselves: Backtracking

Okay, let's see if we can duplicate what regex is actually doing here. 

```rust
#[aoc(day19, part1, backtracking)]
fn part1_backtracking(input: &str) -> usize {
    let puzzle: Puzzle = input.into();

    fn recur(towels: &[&str], target: &str) -> bool {
        if target.is_empty() {
            return true;
        }

        for towel in towels {
            if let Some(rest) = target.strip_prefix(towel) {
                if recur(towels, rest) {
                    return true;
                }
            }
        }

        false
    }

    puzzle
        .targets
        .iter()
        .filter(|target| recur(&puzzle.towels, target))
        .count()
}
```

We'll do a simple enough [[wiki:recursive]]() [[wiki:backtracking]]() solution. For whatever subset of the string we have (until it `is_empty`), try each substring (`towel`). If the string starts with that, `recur`. 

And... we're waiting.

...and waiting. 

...and waiting. 

And I give up. 

There's a perfect example of a [[wiki:ReDoS|regular expression denial of service (ReDoS)]]() attack here. At least one (multiple actually) of the cases fail really far down the backtracking tree and fail *hard*. This... is not efficient. 

We can do a bit better though. 

### Optimization 1: Simplified backtracking

One thing to not about our input is that we have a lot of repeated cases. There are 173 repeating strings, but of those... all but 22 can be made as a combination of other strings. We have no need to check `rgb` if we have `r`, `g`, and `b` as cases. This does mean we're recurring a lot more, but it also means that the branching factor at any individual state is *far* smaller. 

Let's see it:

```rust
#[aoc(day19, part1, bt_simplified)]
fn part1_bt_simplified(input: &str) -> usize {
    let puzzle: Puzzle = input.into();

    // Remove any towels that can be created by a combination of other towels
    let mut towels = puzzle.towels.clone();
    let mut i = 0;
    while i < towels.len() {
        let mut subtowels = towels.clone();
        subtowels.remove(i);

        if recur(&subtowels, towels[i]) {
            towels.remove(i);
        } else {
            i += 1;
        }
    }

    fn recur(towels: &[&str], target: &str) -> bool {
        if target.is_empty() {
            return true;
        }

        for towel in towels {
            if let Some(rest) = target.strip_prefix(towel) {
                if recur(towels, rest) {
                    return true;
                }
            }
        }

        false
    }

    puzzle
        .targets
        .iter()
        .filter(|target| recur(&towels, target))
        .count()
}
```

And how's it do?

```bash
$ AOC 2024
Day 19 - Part 1 - regex : 336
	generator: 125ns,
	runner: 5.632208ms

Day 19 - Part 1 - bt_simplified : 336
	generator: 34.417µs,
	runner: 30.939375ms
```

Alllllll righty then. At least we're ±1 order of magnitude, that's pretty cool. 

I expect that manually compiling this to a state machine would really be the way to go here, but for the moment, let's look at part 2 instead. 

### Optimization 2: Memoization

Okay, after writing up [part 2](#part-2) and thinking about it a bit more while doing other things, I realize that my original assumption that memoization wouldn't help at all because we we only need to return the first value was wrong! We *can* memoize--we just need to memoize any substrings we find that we *know* can't be made. 

```rust
#[aoc(day19, part1, bt_memo)]
fn part1_bt_memo(input: &str) -> usize {
    let puzzle: Puzzle = input.into();
    let mut cache = HashSet::new();

    fn recur<'input>(cache: &mut HashSet<&'input str>, towels: &[&str], target: &'input str) -> bool {
        if target.is_empty() {
            return true;
        }

        if cache.contains(target) {
            return false;
        }

        for towel in towels {
            if let Some(rest) = target.strip_prefix(towel) {
                if recur(cache, towels, rest) {
                    return true;
                }
            }
        }

        cache.insert(target);
        false
    }

    puzzle
        .targets
        .iter()
        .filter(|target| recur(&mut cache, &puzzle.towels, target))
        .count()
}
```

That looks very strange, but totally works! Storing the `&str` in the `HashSet` is an interesting one, because Rust really wants to know what the lifetime of those strings are. Which is exactly why I am tying it to be the same lifetime as the `target: &'input str`. Both live the same time (since they're the same string!)

And how does it compare? 

```bash
$ AOC 2024
Day 19 - Part 1 - regex : 336
	generator: 125ns,
	runner: 5.632208ms

Day 19 - Part 1 - bt_simplified : 336
	generator: 34.417µs,
	runner: 30.939375ms

Day 19 - Part 1 - bt_memo : 336
	generator: 167ns,
	runner: 15.559042ms
```

Well. The regex crate is still faster, but I did cut the simplified version in half! 

I did also try combining the two (simplified + memo), but that ends up not being any faster. We're basically gaining the same reduced branching factor either way. 

Okay, onward for real this time!

## Part 2

> How many possible ways are there to make each string? 

Well *there* is somewhere that a regular expression is not going to work! (by default). You can just count them up with a backtracking solution quickly enough:

```rust
#[aoc(day19, part2, backtracking)]
fn part2_backtracking(input: &str) -> usize {
    let puzzle: Puzzle = input.into();

    fn recur(towels: &[&str], target: &str) -> usize {
        if target.is_empty() {
            return 1;
        }

        let mut count = 0;

        for towel in towels {
            if let Some(rest) = target.strip_prefix(towel) {
                count += recur(towels, rest);
            }
        }

        count
    }

    puzzle
        .targets
        .iter()
        .map(|target| recur(&puzzle.towels, target))
        .sum()
}
```

But if that didn't even finish in [part 1](#lets-write-it-ourselves-backtracking)... I don't have much hope. 

Let's [[wiki:memoization|memoize it]]()!

```rust
#[aoc(day19, part2, bt_memo)]
pub fn part2_backtracking_memo(input: &str) -> usize {
    let puzzle: Puzzle = input.into();

    fn recur<'input>(
        cache: &mut HashMap<&'input str, usize>,
        towels: &[&str],
        target: &'input str,
    ) -> usize {
        // Base case: empty tests are makeable exactly 1 way
        if target.is_empty() {
            return 1;
        }

        // If we've already calculated this target, return the cached value
        // Memoization yo
        if let Some(&count) = cache.get(target) {
            return count;
        }

        // Try each towel and recur on the first occurrence of that towel in the target
        let mut count = 0;

        for towel in towels {
            if let Some(rest) = target.strip_prefix(towel) {
                count += recur(cache, towels, rest);
            }
        }

        cache.insert(target, count);
        count
    }

    let mut cache = HashMap::new();

    puzzle
        .targets
        .iter()
        .map(|target| recur(&mut cache, &puzzle.towels, target))
        .sum()
}
```

Here's how it works without memoization:

<video controls src="/embeds/2024/aoc/day19-no_memo.mp4"></video>

Look at how much work that is doing right at the end of the string. We figure it out one time... and we do it again and again. A perfect case of memoization!

Here it is with memoization:

<video controls src="/embeds/2024/aoc/day19-memo.mp4"></video>

Side by side:

<video controls src="/embeds/2024/aoc/day19.mp4"></video>

We even make it through several words while the non-memo version is still working through the first one!

```bash
$ cargo aoc --day 19 --part 2

AOC 2024
Day 19 - Part 2 - bt_memo : 758890600222015
	generator: 15.917µs,
	runner: 44.942833ms
```

Not so bad. 

## Benchmarks

```bash
$ cargo aoc bench --day 19

Day19 - Part1/regex             time:   [2.3272 ms 2.3387 ms 2.3520 ms]
Day19 - Part1/bt_simplified     time:   [11.778 ms 11.826 ms 11.882 ms]
Day19 - Part1/bt_memo           time:   [6.7616 ms 6.8033 ms 6.8641 ms]

Day19 - Part2/bt_memo           time:   [28.469 ms 28.573 ms 28.688 ms]
```