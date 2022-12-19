---
title: "AoC 2022 Day 1: Calorinator"
date: 2022-12-01 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Calorie Counting](https://adventofcode.com/2022/day/1)

## Part 1

> Given multiple lists of numbers, find the list with the largest sum. 

<!--more-->

Stylistically, I want to 'over engineer' all of the solutions this year, making structs and functions on those structs that act as they 'should'. We'll see how that goes. For this problem, the lists in the input represent Elves with a list of snacks with so many calories. 

So we'll make an Elf:

```rust
#[derive(Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Debug)]
struct Elf {
    calories: i32,
}

impl Elf {
    fn new() -> Self {
        Elf{calories: 0}
    }
}
```

I know that I need the elves to be sortable (since I want the largest), thus `Eq`, `PartialEq`, `Ord`, and `PartialOrd`. Once that's in place, we want a function to read an input file into a list of Elves:

```rust
fn read(filename: &Path) -> Vec<Elf> {
    let mut elves = Vec::new();
    let mut current = Elf::new();

    for line in read_lines(filename) {
        if line.len() == 0 {
            elves.push(current);
            current = Elf::new();
        } else {
            current.calories += line.parse::<i32>().unwrap();
        }
    }
    elves.push(current);

    return elves;
}
```

And with all that boilerplate out of the way, it's not much code at all to solve part 1:

```rust
fn part1(filename: &Path) -> String {
    let elves = read(filename);
    elves
        .iter()
        .max()
        .expect("no Elves found, can't take max")
        .calories
        .to_string()
}
```

The `expect` never actually fires, since we always have at least 1 Elf with 0 calories, but so it goes. 

Using our test function:

```rust
#[test]   
fn test1() { aoc_test("01", part1, "70369") }
```

And it's of course crazy fast:

```bash
$ cargo build --bin 01-calorinator --release

   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished release [optimized] target(s) in 0.43s

$ ./target/release/01-calorinator 1 data/01.txt

70369
took 1.065458ms
```

## Part 2

> Find the total of the three lists with the individual largest sums. 

That's kind of neat. I feel like implementing {{<doc rust Sum>}} should do it. (Yes, I could just explicitly get the top 3). Unfortunately, I can't get that one for free. But it's clean enough to write:

```rust
impl Sum for Elf {
    fn sum<I: Iterator<Item = Self>>(iter: I) -> Self {
        let mut calories = 0;
        for elf in iter {
            calories += elf.calories;
        }
        Elf{calories}
    }
}
```

And then getting the 3 largest and summing them:

```rust
fn part2(filename: &Path) -> String {
    let mut elves = read(filename);
    
    elves.sort();
    elves.reverse();

    elves.into_iter().take(3).sum::<Elf>().calories.to_string()
}
```

And running it:

```bash
$ ./target/release/01-calorinator 2 data/01.txt

203002
took 421.041µs
```

Cool. Onward!