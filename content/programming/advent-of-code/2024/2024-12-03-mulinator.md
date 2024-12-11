---
title: "AoC 2024 Day 3: Mulinator"
date: 2024-12-03 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- State Machine
- Parsing
---
## Source: [Day 3: Mull It Over](https://adventofcode.com/2024/day/3)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day3.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a string containing (among other gibberish) commands of the form `mul({A}, {B})` where `{A}` and `{B}` are integers, calculate the sum of `A*B`s.

<!--more-->

Simple parsing, ignoreing other input? Seems like a job for a [[wiki:regular expression]]()!

```rust
#[aoc(day3, part1, regex)]
fn part1_regex(input: &str) -> u32 {
    let re = Regex::new(r"mul\((\d{1,3}),(\d{1,3})\)").unwrap();

    re.captures_iter(input)
        .map(|c| c[1].parse::<u32>().unwrap() * c[2].parse::<u32>().unwrap())
        .sum::<u32>()
}
```

Yup, that's it. Create a regex that matches the literal `mul(`, a number (it does specify in the problem that they're 1-3 digits, which is actually unusual for AoC to specify), the `,`, another number, and then the `)`. Then, for each, parse as `u32`, multiply, and sum at the end. 

```bash
cargo aoc --day 3 --part 1

Day 3 - Part 1 - regex : 174336360
	generator: 83ns,
	runner: 1.4465ms
```

*What!?* **Milliseconds?!**

We can do better.

### Optimization 1: Use `nom`

Okay, regular expressions are cool and all, but let's try something a bit lower level. Like... [[wiki:parser combinators]]()! Enter [`nom`](https://docs.rs/nom/latest/nom/).

😋

```rust
#[aoc(day3, part1, nom)]
fn part1_nom(input: &str) -> u32 {
    many1(many_till(
        anychar::<_, (_, nom::error::ErrorKind)>,
        delimited(
            tag("mul("),
            separated_pair(complete::u32, tag(","), complete::u32),
            tag(")"),
        ),
    ))(input)
    .unwrap()
    .1
    .iter()
    .map(|(_, (a, b))| a * b)
    .sum()
}
```

That's a bit of a mess, but it's expecting:

* `many1` - multiple inputs
* `many_till` - each of which can have any number of any character (`anychar`) before them
  * (Side note: The typechecker needed some help here, which I wasn't thrilled with)
* Then, `delimited` by `char(` and `)`, we have a `pair` of `u32`, `separated` by a `,`

Take that, `unwrap` (ignore!) any errors, drop any remaining input (the `.1`), and `map` each `many1` result. In there, we drop the `anychar` and only keep the pair as `(a, b)`. Bit crazy looking, but that's it. 

```bash
$ cargo aoc --day 3 --part 1

Day 3 - Part 1 - regex : 174336360
	generator: 83ns,
	runner: 1.4465ms

Day 3 - Part 1 - nom : 174336360
	generator: 292ns,
	runner: 424.75µs
```

So how does it perform? Twice as fast! And we're back under 1ms. 

But I think we can do even better.

### Optimization 2: Manual parsing / state machine

`nom` is a parser combinator library and, as such, has a ton of function calls, error handling, and backtracking built in. But for what we're doing, we don't need any of that. 

Instead, let's manually write a loop with a [[wiki:state machine]]() to do our parsing:

```rust
#[aoc(day3, part1, iterator)]
fn part1(input: &str) -> u32 {
    let input = input.chars().collect::<Vec<_>>();

    #[derive(Debug)]
    enum State {
        Scanning,
        ReadingA,
        ReadingB,
    }

    let mut sum = 0;
    let mut a = 0;
    let mut b = 0;

    let mut state = State::Scanning;
    let mut index = 0;

    loop {
        match state {
            State::Scanning => {
                if input[index..].starts_with(&['m', 'u', 'l', '(']) {
                    state = State::ReadingA;
                    a = 0;
                    b = 0;
                    index += 3;
                }
            }
            State::ReadingA => {
                if input[index] == ',' {
                    state = State::ReadingB;
                } else if input[index].is_ascii_digit() {
                    a = a * 10 + input[index] as u32 - '0' as u32;
                } else {
                    state = State::Scanning;
                    index -= 1; // Recheck incase we start another mul
                }
            }
            State::ReadingB => {
                if input[index] == ')' {
                    sum += a * b;
                    state = State::Scanning;
                } else if input[index].is_ascii_digit() {
                    b = b * 10 + input[index] as u32 - '0' as u32;
                } else {
                    state = State::Scanning;
                    index -= 1; // Recheck incase we start another mul
                }
            }
        }

        index += 1;
        if index >= input.len() {
            break;
        }
    }

    sum
}
```

In this case, we start in `Scanning` until we find a `mul(`. Once we do, we are `ReadingA` until we see a `,` sending us to `ReadingB` or bad input, sending us back to `Scanning`. Then, the same for `ReadingB` until we see the `)`. If we get that far, add the product to the sum and back we go!

It's... quite a bit longer and I would argue not nearly as easy to read. And unless you are dealing with many (many) inputs, you really do want something a bit simpler than this. Is that the regex above? Well, that depends I suppose on how easy you think regex are to read. 

But it is faster:

```bash
$ cargo aoc --day 3 --part 1

AOC 2024

Day 3 - Part 1 - regex : 174336360
	generator: 83ns,
	runner: 1.4465ms

Day 3 - Part 1 - nom : 174336360
	generator: 292ns,
	runner: 424.75µs

Day 3 - Part 1 - iterator : 174336360
	generator: 14.791µs,
	runner: 124.834µs
```

That's another ~3x speedup even over the `nom` solution, 6x as fast as our regex. That's pretty neat. 

## Part 2

> Add two additional commands:
>   1. When you see `don't()`, ignore all `mul(...)` commands
>   2. When you see `do()`, start paying attention to them again

Okay. That's easy enough to parse with our regular expressions, but when it comes to actually keeping state and evaluating this, it's a bit trickier. 

What we really want for something that runs across a list of input and keeps state is to swap out our `map` for `fold`:

```rust
#[aoc(day3, part2, regex)]
fn part2_regex(input: &str) -> u32 {
    let re = Regex::new(r"mul\((\d{1,3}),(\d{1,3})\)|do\(\)|don't\(\)").unwrap();

    re.captures_iter(input)
        .fold((0, true), |(sum, capturing), cap| match &cap[0] {
            "do()" => (sum, true),
            "don't()" => (sum, false),
            _ if capturing => (
                sum + cap[1].parse::<u32>().unwrap() * cap[2].parse::<u32>().unwrap(),
                capturing,
            ),
            _ => (sum, capturing),
        })
        .0
}
```

For each element, we'll keep track of a `(sum, capturing)` flag. `do` and `don't` don't do anything but they do change the status of the flag. `mul` is the only other case, but now we only bother `parse::<u32>` and summing if we're `capturing`.

Then, drop the flag with the `.0` and we're golden!

I bet you can see where this is going next though :smile:.

For this, I just skipped `nom` and went straight to the state machine form:

```rust
#[aoc(day3, part2, iterator)]
fn part2(input: &str) -> u32 {
    let input = input.chars().collect::<Vec<_>>();

    #[derive(Debug)]
    enum State {
        Scanning,
        Disabled,
        ReadingA,
        ReadingB,
    }

    let mut sum = 0;
    let mut a = 0;
    let mut b = 0;

    let mut state = State::Scanning;
    let mut index = 0;

    loop {
        match state {
            State::Scanning => {
                if input[index..].starts_with(&['m', 'u', 'l', '(']) {
                    state = State::ReadingA;
                    a = 0;
                    b = 0;
                    index += 3;
                } else if input[index..].starts_with(&['d', 'o', 'n', '\'', 't', '(', ')']) {
                    state = State::Disabled;
                    index += 6;
                }
            }
            State::Disabled => {
                if input[index..].starts_with(&['d', 'o', '(', ')']) {
                    state = State::Scanning;
                    index += 3;
                }
            }
            State::ReadingA => {
                if input[index] == ',' {
                    state = State::ReadingB;
                } else if input[index].is_ascii_digit() {
                    a = a * 10 + input[index] as u32 - '0' as u32;
                } else {
                    state = State::Scanning;
                    index -= 1; // Recheck incase we start another mul
                }
            }
            State::ReadingB => {
                if input[index] == ')' {
                    sum += a * b;
                    state = State::Scanning;
                } else if input[index].is_ascii_digit() {
                    b = b * 10 + input[index] as u32 - '0' as u32;
                } else {
                    state = State::Scanning;
                    index -= 1; // Recheck incase we start another mul
                }
            }
        }

        index += 1;
        if index >= input.len() {
            break;
        }
    }

    sum
}
```

For the most part, the parser is the same as what we've seen before, but there are a few additional states and cases to consider:

* We only case about `don't()` if we're in the `Scanning` state; this will swap us into the new `Disabled` state
* If we're in that state, only look for `do()` to go back to `Scanning` -- by ignoring `mul` entirely in this state, we should gain a bit more performance

Running them both:

```bash
$ cargo aoc --day 3 --part 2

AOC 2024

Day 3 - Part 2 - regex : 88802350
	generator: 84ns,
	runner: 2.092541ms

Day 3 - Part 2 - iterator : 88802350
	generator: 18.583µs,
	runner: 215.667µs
```

Roughly 6x speedup once again! It is ~twice as slow as the first parser, which is unfortunate, but it's still well under 1ms, so we'll go ahead with this for now. 

## Benchmarks

Overall timing using `cargo aoc bench`:

```bash
$ cargo aoc bench --day 3
Day3 - Part1/iterator   time:   [31.657 µs 31.891 µs 32.270 µs]
Day3 - Part1/nom        time:   [108.02 µs 108.26 µs 108.50 µs]
Day3 - Part1/regex      time:   [241.65 µs 242.97 µs 244.34 µs]
Day3 - Part2/iterator   time:   [54.213 µs 55.198 µs 56.174 µs]
Day3 - Part2/regex      time:   [293.66 µs 313.42 µs 354.22 µs]
```

Fast enough. Onward!