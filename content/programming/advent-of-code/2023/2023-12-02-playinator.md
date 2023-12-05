---
title: "AoC 2023 Day 2: Playinator"
date: 2023-12-02 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 2: Cube Conundrum](https://adventofcode.com/2023/day/2)

## Part 1

> Play a game where you have some number of red, green, and blue dice in a cup, which you draw and roll (without replacement). Which game is possible with only 12 red, 13 gree, and 14 blue cubes? 

Input will look like: `Game 1: 3 blue, 4 red; 1 red, 2 green, 6 blue; 2 green`

<!--more-->

Okay, start with the data. What do we expect the (parsed) simulation would look like?

```rust
// A game consists of an ID and some number of rounds each with some number of dice
#[derive(Debug, PartialEq)]
pub struct Game {
    id: u32,
    rounds: Vec<Round>,
}

// A single round can have some number each of red/green/blue dice
#[derive(Debug, PartialEq)]
pub struct Round {
    red: u32,
    green: u32,
    blue: u32,
}

// Represents colors of dice
#[derive(Debug, PartialEq)]
pub enum Colors {
    Red,
    Green,
    Blue,
}
```

Next step to get there, I've heard good things about this [`nom` crate](https://crates.io/crates/nom). Let's try parsing with it. 

In order to not pollute my main namespace with imports from `nom`, I'm going to make an internal `parse` module:

```rust
mod parse {
    use crate::*;
    use nom::{
        branch::*, bytes::complete::*, character::complete, character::complete::newline,
        combinator::*, multi::*, sequence::*, *,
    };

    pub fn games(s: &str) -> IResult<&str, Vec<Game>> {
        separated_list1(newline, game)(s)
    }

    fn game(s: &str) -> IResult<&str, Game> {
        let (s, _) = tag("Game ")(s)?;
        let (s, id) = complete::u32(s)?;
        let (s, _) = tag(": ")(s)?;

        let (s, rounds) = separated_list1(tag("; "), round)(s)?;

        Ok((s, Game { id, rounds }))
    }

    fn round(s: &str) -> IResult<&str, Round> {
        let (s, counts) = separated_list1(
            tag(", "),
            sequence::tuple((complete::u32, preceded(tag(" "), color))),
        )(s)?;

        let mut red = 0;
        let mut green = 0;
        let mut blue = 0;

        for (count, color) in counts {
            match color {
                Colors::Red => red = count,
                Colors::Green => green = count,
                Colors::Blue => blue = count,
            }
        }

        Ok((s, Round { red, green, blue }))
    }

    fn color(s: &str) -> IResult<&str, Colors> {
        alt((
            map(tag("red"), |_| Colors::Red),
            map(tag("green"), |_| Colors::Green),
            map(tag("blue"), |_| Colors::Blue),
        ))(s)
    }

    #[cfg(test)]
    mod tests {
        // ...
    }
}
```

You know, I can of like that! It's a bit more verbose than a pile of `split` and `parse` calls, but it's fairly self contained and directly returns the data structure. Plus, with this we can just call `parse::games` to get the `Vec<Game>`, find any that match the conditions (there should be exactly one) and return it:

```rust
fn part1(filename: &Path) -> Result<String> {
    let input = read_to_string(filename)?;
    let (_, games) = parse::games(&input).unwrap();

    // Return sum of ID of game that contained no more than
    // 12 red cubes, 13 green cubes, and 14 blue cubes
    Ok(games
        .into_iter()
        .filter(|game| {
            game.rounds
                .iter()
                .all(|round| round.red <= 12 && round.green <= 13 && round.blue <= 14)
        })
        .map(|game| game.id)
        .sum::<u32>()
        .to_string())
}
```

I did a `sum`, but a `.next().unwrap()` would have worked much the same. 

## Part 2

> Find the fewest number of cubes possible for each game. For each game, multiply those three numbers together and then sum these products. 

We already have everything we need here, if we add a `power` method on `Game`:

```rust
// The power of a game is the product of the minumum number of cubes of each color
impl Game {
    fn power(&self) -> u32 {
        self.rounds
            .iter()
            .fold([0, 0, 0], |acc, round| {
                [
                    acc[0].max(round.red),
                    acc[1].max(round.green),
                    acc[2].max(round.blue),
                ]
            })
            .into_iter()
            .product()
    }
}
```

We're going to [[wiki:fold]]() across the games, keeping track of each maximum (red, green, and blue) independently, then `product` at the end. Sum those and we're golden:

```rust
fn part2(filename: &Path) -> Result<String> {
    let input = read_to_string(filename)?;
    let (_, games) = parse::games(&input).unwrap();

    // Calculate the sum of powers of the rounds
    Ok(games
        .into_iter()
        .map(|game| game.power())
        .sum::<u32>()
        .to_string())
}
```

## Performance

Still microseconds:

```bash
$ cargo run --release --bin 02-playinator 1 data/02.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/02-playinator 1 data/02.txt`
2061
took 217.709µs

$ cargo run --release --bin 02-playinator 2 data/02.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/02-playinator 2 data/02.txt`
72596
took 58.167µs
```