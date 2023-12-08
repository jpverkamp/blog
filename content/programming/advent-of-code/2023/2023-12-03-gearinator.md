---
title: "AoC 2023 Day 3: Gearinator"
date: 2023-12-03 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 3: Gear Ratios](https://adventofcode.com/2023/day/3)

{{<toc>}}

## Part 1

> Take as input a 2D grid of numbers or symbols (`.` represents empty space). Numbers will be 1 or more digits written horizontally which should be concatenated (`.467*` is the number `467` followed by the symbol `*`). 
>
> Sum all numbers that are adjacent (including diagonally) to at least one symbol. 

<!--more-->

Okay, first our data structure (including an `is_neighbor` function I'm sure will be helpful):

```rust
#[derive(Debug)]
struct Number {
    value: usize,
    x_min: usize,
    x_max: usize,
    y: usize,
}

impl Number {
    fn is_neighbor(&self, x: usize, y: usize) -> bool {
        x + 1 >= self.x_min && x <= self.x_max && y + 1 >= self.y && y <= self.y + 1
    }
}

#[derive(Debug)]
struct Symbol {
    value: char,
    x: usize,
    y: usize,
}

#[derive(Debug)]
struct Schematic {
    numbers: Vec<Number>,
    symbols: Vec<Symbol>,
}
```

In this case, the `x_min` is inclusive and `x_max` is exclusive, so in the example above of `.467*`, `x_min = 1` and `x_max = 4`. 

Next, a function to read a `String` into this `Schematic`:

```rust
impl From<String> for Schematic {
    fn from(value: String) -> Self {
        let mut numbers = Vec::new();
        let mut symbols = Vec::new();

        fn finish_number(
            numbers: &mut Vec<Number>,
            digits: &mut String,
            x_min: usize,
            x_max: usize,
            y: usize,
        ) {
            if digits.is_empty() {
                return;
            }

            let value = digits.parse::<usize>().unwrap();
            digits.clear();
            numbers.push(Number {
                value,
                x_min,
                x_max,
                y,
            });
        }

        for (y, line) in value.lines().enumerate() {
            let mut digits = String::new();
            let mut x_min = 0;

            for (x, c) in line.chars().enumerate() {
                if c.is_ascii_digit() {
                    if digits.is_empty() {
                        x_min = x;
                    }
                    digits.push(c);
                } else if c == '.' {
                    finish_number(&mut numbers, &mut digits, x_min, x, y);
                } else {
                    finish_number(&mut numbers, &mut digits, x_min, x, y);
                    symbols.push(Symbol { value: c, x, y });
                }
            }
            finish_number(&mut numbers, &mut digits, x_min, line.len(), y);
        }

        Schematic { numbers, symbols }
    }
}
```

I wish I could have done a `nom` parser for this as well, but I've real idea how to keep track of row/column in that case, so this will have to do. 

One interesting thing here is the `finish_number` function. Since a number might end with a `.`, a symbol, or the end of a line, it helps to e4xtract that into a helper function to avoid duplicating code. 

Okay, we have the data, so how do we find `Numbers` adjacent to `Symbols`? 

```rust
fn part1(filename: &Path) -> Result<String> {
    let schematic = Schematic::from(read_to_string(filename)?);

    Ok(schematic
        .numbers
        .iter()
        .filter(|n| schematic.symbols.iter().any(|s| n.is_neighbor(s.x, s.y)))
        .map(|n| n.value)
        .sum::<usize>()
        .to_string())
}
```

I love functional style Rust. :D We literally `filter` by `is_neighbor`, `map` out the value (I could have used a `filter_map`, but I think in this case, this is more readable) and `sum` them.

Voila.

## Part 2

> Find all numbers adjacent to exactly two `*` `Symbols`. Multiply the two numbers and sum all of these products. 

```rust
fn part2(filename: &Path) -> Result<String> {
    let schematic = Schematic::from(read_to_string(filename)?);

    Ok(schematic
        .symbols
        .iter()
        .filter(|s| s.value == '*')
        .map(|s| {
            schematic
                .numbers
                .iter()
                .filter_map(|n| {
                    if n.is_neighbor(s.x, s.y) {
                        Some(n.value)
                    } else {
                        None
                    }
                })
                .collect::<Vec<_>>()
        })
        .filter(|ratios| ratios.len() == 2)
        .map(|ratios| ratios[0] * ratios[1])
        .sum::<usize>()
        .to_string())
}
```

Not going to lie, it's a bit funny looking. Basically, we're going to take the list of symbols, `filter` out any that aren't `*`, `map` to get the neighboring numbers, `filter` out any that don't have exactly two, and `map` to calculate the product. 

Fun!

## Performance

```bash
$ cargo run --release --bin 03-gearinator 1 data/03.txt

    Finished release [optimized] target(s) in 0.01s
     Running `target/release/03-gearinator 1 data/03.txt`
549908
took 411.292µs

$ cargo run --release --bin 03-gearinator 2 data/03.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/03-gearinator 2 data/03.txt`
81166799
took 509.75µs
```

Still micros! Onward!