---
title: "AoC 2023 Day 4: Scratchinator"
date: 2023-12-04 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 4: Scratchcards](https://adventofcode.com/2023/day/4)

{{<toc>}}

## Part 1

> Simulate [[wiki:scratchcards]](). Given a list of winning numbers and guessed numbers, count how many guessed numbers are in the winning list. Your score is 1, 2, 4, 8, ... for 1, 2, 3, 4, ... matching numbers. 

<!--more-->

Okay, data structure:

```rust
#[allow(dead_code)]
#[derive(Debug)]
pub struct Card {
    pub id: u32,
    pub winning_numbers: Vec<u8>,
    pub guesses: Vec<u8>,
}

impl Card {
    fn matches(&self) -> usize {
        self.guesses
            .iter()
            .filter(|guess: &&u8| self.winning_numbers.contains(guess))
            .count()
    }
}
```

This includes the matches function. We're using `Vec<u8>` here, although a `HashSet` or `BTreeSet` might be slightly more performant. I don't think that (at this scale) it really matters, although being able to use `.intersect(...)` would be nice.

Now `nom` for parsing:

```rust
mod parse {
    use crate::*;
    use nom::{
        bytes::complete::*,
        character::complete,
        character::complete::{newline, space0, space1},
        multi::*,
        sequence::*,
        *,
    };

    pub fn cards(s: &str) -> IResult<&str, Vec<Card>> {
        separated_list1(newline, card)(s)
    }

    fn card(s: &str) -> IResult<&str, Card> {
        let (s, _) = tag("Card")(s)?;
        let (s, _) = space1(s)?;
        let (s, id) = complete::u32(s)?;
        let (s, _) = tag(":")(s)?;
        let (s, _) = space0(s)?;
        let (s, winning_numbers) = separated_list1(space1, complete::u8)(s)?;
        let (s, _) = delimited(space0, tag("|"), space0)(s)?;
        let (s, guesses) = separated_list1(space1, complete::u8)(s)?;

        Ok((
            s,
            Card {
                id,
                winning_numbers,
                guesses,
            },
        ))
    }

    #[cfg(test)]
    mod test {
        // ...
    }
}
```

The sequence of parsers is a bit ugly, but I'm not sure a better way to do that. I could probably handle it with a nom tuple, but then I still have to ignore the right values. As it is, we get a list for each value, so we can just push it out:

```rust
fn part1(filename: &Path) -> Result<String> {
    let input = read_to_string(filename)?;
    let (_, cards) = parse::cards(&input).unwrap();

    // Wrapper to avoid calculating 2^(-1) or 2^(usize::MAX)
    fn score(matches: usize) -> usize {
        if matches == 0 {
            0
        } else {
            2_usize.pow((matches - 1) as u32)
        }
    }

    Ok(cards
        .iter()
        .map(|card| score(card.matches()))
        .sum::<usize>()
        .to_string())
}
```

And that's it! 

## Part 2

> Instead of scoring each card, take the number of matches for each card and gain that many of the next cards (so if Card 5 scores 3, add one each of Card 6, 7, 8). 
>
> Count the total number of cards once you are not gaining any more.
>
> You may assume that you won't be asked to gain cards that don't exist (off the end of the list). 

Because each card only adds future cards, we can probably do this in one pass. But my first solution was instead to go through and `loop` until the simulation stabilizes. Certainly not a very functional model!

```rust
fn part2(filename: &Path) -> Result<String> {
    let input = read_to_string(filename)?;
    let (_, cards) = parse::cards(&input).unwrap();

    let mut total = 0;
    let mut counts = vec![1; cards.len()];
    let mut next_counts = vec![0; cards.len()];

    // Earn new cards until stable
    loop {
        // Count all cards earned before updating
        total += counts.iter().sum::<usize>();

        // Each card earns
        // NOTE: We're explicitly guaranteed that next_counts[i + j + 1] doesn't overflow
        for (i, card) in cards.iter().enumerate() {
            for j in 0..card.matches() {
                next_counts[i + j + 1] += counts[i];
            }
        }

        // If no cards were earned, we're done
        if next_counts.iter().all(|&c| c == 0) {
            break;
        }

        // Swap buffers and clear
        // This could be a std::mem::swap, but we'd still need to init the new next_counts
        for i in 0..cards.len() {
            counts[i] = next_counts[i];
            next_counts[i] = 0;
        }
    }

    Ok(total.to_string())
}
```

But...

## Performance

```bash
$ cargo run --release --bin 04-scratchinator 1 data/04.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/04-scratchinator 1 data/04.txt`
23028
took 142.75µs

$ cargo run --release --bin 04-scratchinator 2 data/04.txt

    Finished release [optimized] target(s) in 0.00s
     Running `target/release/04-scratchinator 2 data/04.txt`
9236992
took 696µs
```

It still runs in microseconds. So I don't feel much need to optimize it. 

Onward!