---
title: "AoC 2022 Day 2: Roshamboinator"
date: 2022-12-02 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
## Source: [Rock Paper Scissors](https://adventofcode.com/2022/day/2)

## Part 1

> Given a list of Rock Paper Scissors matches with A,B,C or X,Y,Z corresponding to those plays and scoring 1,2,3 points for your play plus 0,3,6 for a loss, draw, or win, what is your total score. 

<!--more-->

Cool. Let's over engineer it!

First, a `Play` and an `Outcome`:

```rust
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
enum Play {
    Rock,
    Paper,
    Scissors,
}

#[derive(Copy, Clone, Debug)]
enum Outcome {
    Lose,
    Draw,
    Win,
}
```

Now, for `Play`, we want to be able to build them from the input values, get the `value` of any play, or determine the `Outcome` for a match:

```rust
impl Play {
    fn new(c: char) -> Play {
        use Play::*;

        match c {
            'A' | 'X' => Rock,
            'B' | 'Y' => Paper,
            'C' | 'Z' => Scissors,
            _ => panic!("unknown play: {:?}", c),
        }
    }

    fn value(self) -> i32 {
        use Play::*;

        match self {
            Rock => 1,
            Paper => 2,
            Scissors => 3,
        }
    }

    fn vs(self, other: Play) -> Outcome {
        use Outcome::*;
        use Play::*;

        match (self, other) {
            (a, b) if a == b => Draw,

            (Rock, Scissors) | (Scissors, Paper) | (Paper, Rock) => Win,

            _ => Lose,
        }
    }
}
```

The `vs` function is my favorite. I previously hadn't gotten to use multiple cases in a match (with `|`) or guards (with `if`). Pretty powerful syntax there. I do love languages with solid pattern matching. 

Next, we need the value for `Outcome` as well:

```rust
impl Outcome {
    fn value(self) -> i32 {
        use Outcome::*;
        
        match self {
            Lose => 0,
            Draw => 3,
            Win => 6,
        }
    }
}
```

And then we should be able to parse the input and calculate a score:

```rust
fn part1(filename: &Path) -> String {
    let mut total_score = 0;

    for line in read_lines(filename) {
        let them = Play::new(line.chars().nth(0).expect("must have 1 char per line"));
        let us = Play::new(line.chars().nth(2).expect("must have 3 chars per line"));

        total_score += us.value() + us.vs(them).value();
    }
    
    total_score.to_string()
}
```

It's not a bit weird to use `nth` to pull out the chars, but I was having some issues with `String` vs `&str` comparisons. Chars just work. 

Run it on my input:

```bash
$ ./target/release/02-roshamboinator 1 data/02.txt

13446
took 752.791µs
```

Cool. 

## Part 2

> Now treat input X,Y,Z as you needing to lose, draw, or win respectively. Determine the move that gives that outcome and calculate the score as before. 

We have most of this, but we do need a new constructor to load the `Outcome`:

```rust
impl Outcome {
    fn new(c: char) -> Outcome {
        use Outcome::*;

        match c {
            'X' => Lose,
            'Y' => Draw,
            'Z' => Win,
            _ => panic!("unknown outcome: {:?}", c)
        }
    }
}
```

And now we can actually determine the plays:

```rust
fn part2(filename: &Path) -> String {
    use Outcome::*;
    use Play::*;

    let mut total_score = 0;

    for line in read_lines(filename) {
        let them = Play::new(line.chars().nth(0).expect("must have 1 char per line"));
        let goal = Outcome::new(line.chars().nth(2).expect("must have 3 chars per line"));

        let us = match goal {
            Lose => match them {
                Rock => Scissors,
                Scissors => Paper,
                Paper => Rock,
            },
            Draw => them,
            Win => match them {
                Rock => Paper,
                Scissors => Rock,
                Paper => Scissors,
            },
        };

        total_score += us.value() + goal.value();
    }

    total_score.to_string()
}
```

It's a bit more in teh actual part, mostly because we need to have a nested `match` to determine what the `us` play is. But once we have that, the `total_score` calculation is the same. 


```bash
$ ./target/release/02-roshamboinator 2 data/02.txt

13509
took 662.916µs
```

Double cool. 