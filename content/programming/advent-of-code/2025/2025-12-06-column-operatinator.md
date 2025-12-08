---
title: "AoC 2025 Day 6: Column Operatinator"
date: 2025-12-06 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 6: Trash Compactor](https://adventofcode.com/2025/day/6)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day6.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given input like this:
>
> ```text
> 123 328  51 64 
>  45 64  387 23 
>   6 98  215 314
> *   +   *   +  
> ```
>
> Apply the operation in each column then sum the results. 

<!--more-->

Okay, let's do this the relatively straightforward way first:

* For each but the last line, split on whitespace and parse as a `Vec<usize>`
* For the `last` line, split on whitespace and keep the operators
* Loop over all of the rows, applying the `operator` to the `numbers`
* Sum those

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let lines = input.lines().collect::<Vec<_>>();

    let numbers = lines[..lines.len() - 1]
        .iter()
        .map(|line| {
            line.split_ascii_whitespace()
                .map(|value| value.parse::<usize>().unwrap())
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    lines
        .last()
        .unwrap()
        .split_ascii_whitespace()
        .enumerate()
        .map(|(i, op)| {
            let values = numbers.iter().map(|line| line[i]);
            match op {
                "*" => values.product::<usize>(),
                "+" => values.sum::<usize>(),
                _ => unimplemented!("Unknown operator {op}"),
            }
        })
        .sum::<usize>()
        .to_string()
}
```

Which works well enough:

```bash
$ just run-and-bench 6 part1

4309240495780
part1: 45.201µs ± 2.998µs [min: 42µs, max: 56.125µs, median: 43.958µs]
```

## Part 2

> Do the same thing, but this time with numbers written vertically.
>
> ```text
> 123 328  51 64 
>  45 64  387 23 
>   6 98  215 314
> *   +   *   +  
> ```
>
> So for the first column, we have `1 * 24 * 356`. 
>
> (The problem statement actually runs right to left, but for `*` and `+`, being [[wiki:commutative]](), this doesn't matter.)

Yeah, I thought we might have to do this. 

Okay, let's use the `Grid` from yesterday to make a `Grid<char>`. Then we can iterate across the grid from left to right until we find an `x`/column where all of the values are spaces. That will give us a single sum or product to do. Then for those, we'll run down the rows, collecting each into a number. 

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let grid = Grid::read(input, |c| c);

    let mut col_start = 0;
    let mut sum = 0;

    for x in 0..=grid.width() {
        // Detected a vertical column of empty spaces at x
        if x == grid.width() || (0..grid.height()).all(|y| grid.get(x, y) == Some(' ')) {
            // Parse out each number in the column, ignore empty spaces
            let numbers = (col_start..x).map(|x| {
                (0..grid.height() - 1).fold(0_usize, |a, y| match grid.get(x, y).unwrap() {
                    '0'..='9' => a * 10 + (grid.get(x, y).unwrap() as usize - '0' as usize),
                    ' ' => a,
                    c => unreachable!("Unknown value {c:?}"),
                })
            });

            // Apply the matching operator, assume it's left aligned
            sum += match grid.get(col_start, grid.height() - 1) {
                Some('*') => numbers.product::<usize>(),
                Some('+') => numbers.sum::<usize>(),
                c => unreachable!("Unknown operator {c:?}"),
            };

            col_start = x + 1;
        }
    }

    sum.to_string()
}
```

The `x == grid.width() ||` detects the ends of lines (we're not necessarily guaranteed a column of spaces at the end). Other than that, the most interesting part is this:

```rust
let numbers = (col_start..x).map(|x| {
    (0..grid.height() - 1).fold(0_usize, |a, y| match grid.get(x, y).unwrap() {
        '0'..='9' => a * 10 + (grid.get(x, y).unwrap() as usize - '0' as usize),
        ' ' => a,
        c => unreachable!("Unknown value {c:?}"),
    })
});
```

This is saying, each number is on a different `x`/column (the outer `.map`) with each digit on a different `y`/row. So the `.fold` will apply across each `x`, `y` that belongs to a number and builds them up basically by parsing as base 10. So if you have `123`, you get `1` => `1 * 10 + 2` => `12 * 10 + 3` => `123`. 

And that's... just it!

```bash
$ just run-and-bench 6 part2

9170286552289

part2: 35.121µs ± 2.746µs [min: 32.417µs, max: 43.458µs, median: 35.208µs]
```

## Part 1 - Grid

You can do the same for part 1, just swapping out the order of the `x` and `y` map:

```rust
// Parse out each number in the column, ignore empty spaces
let numbers = (0..grid.height() - 1).map(|y| {
    (col_start..x).fold(0_usize, |a, x| match grid.get(x, y).unwrap() {
        '0'..='9' => a * 10 + (grid.get(x, y).unwrap() as usize - '0' as usize),
        ' ' => a,
        c => unreachable!("Unknown value {c:?}"),
    })
});
```

The rest is the same as `part2`.

```bash
$ just run-and-bench 6 part1_grid

4309240495780

part1_grid: 34.773µs ± 1.757µs [min: 33.625µs, max: 42.667µs, median: 34.042µs]
```

That's 20% faster, which isn't nothing. But on the other hand, both are running in the sub 100µs range, so it really isn't a big deal either way at this scale of input. 

## Benchmarks

```bash
$ just bench 6

part1: 38.877µs ± 3.178µs [min: 37.5µs, max: 56.042µs, median: 37.709µs]
part1_grid: 39.811µs ± 3.344µs [min: 36.667µs, max: 54.916µs, median: 37.375µs]
part2: 34.372µs ± 1.887µs [min: 31.041µs, max: 40.084µs, median: 35.083µs]
```

What's interesting is that when you run them all together, you actually get slightly slower results for `part1_grid`. But since the error bars on those are both a few µs, this is expected. 

| Day | Part | Solution     | Benchmark          |
| --- | ---- | ------------ | ------------------ |
| 6   | 1    | `part1`      | 38.877µs ± 3.178µs |
| 6   | 1    | `part1_grid` | 39.811µs ± 3.344µs |
| 6   | 2    | `part2`      | 34.372µs ± 1.887µs |