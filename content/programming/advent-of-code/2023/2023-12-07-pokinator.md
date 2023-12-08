---
title: "AoC 2023 Day 7: Pokinator"
date: 2023-12-07 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 7: Camel Cards](https://adventofcode.com/2023/day/7)

{{<toc>}}

## Part 1

> Simulate a limited poker game with no suits and break otherwise tied hands [[wiki:lexicographically]]() (`AAAA2` beats `AKAAA`) because the the hands are both four of a kind, the first cards are both `A`, but the second `A` beats the `K`. It doesn't matter that the first hand's off card was a `2`
>
> Order all hands then calculate the sum of the ordering of hands (1 for best etc) times the bet for each. 

<!--more-->

### Types and Parsing

```rust
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Copy, Clone, Hash)]
pub enum Card {
    Two,
    Three,
    Four,
    Five,
    Six,
    Seven,
    Eight,
    Nine,
    Ten,
    Jack,
    Queen,
    King,
    Ace,
}

impl From<char> for Card {
    fn from(c: char) -> Self {
        match c {
            '2' => Card::Two,
            '3' => Card::Three,
            '4' => Card::Four,
            '5' => Card::Five,
            '6' => Card::Six,
            '7' => Card::Seven,
            '8' => Card::Eight,
            '9' => Card::Nine,
            'T' => Card::Ten,
            'J' => Card::Jack,
            'Q' => Card::Queen,
            'K' => Card::King,
            'A' => Card::Ace,
            _ => panic!("Invalid card: {}", c),
        }
    }
}

#[derive(Debug, PartialEq, Eq, Copy, Clone)]
pub struct Hand {
    pub cards: [Card; 5],
    pub bid: u64,
}

fn hand(s: &str) -> IResult<&str, Hand> {
    let (s, cards) = count(anychar, 5)(s)?;
    let cards = cards.iter().map(|c| Card::from(*c)).collect::<Vec<_>>();
    let (s, _) = space1(s)?;
    let (s, bid) = complete::u64(s)?;

    Ok((
        s,
        Hand {
            cards: cards.try_into().unwrap(),
            bid,
        },
    ))
}

pub fn hands(s: &str) -> IResult<&str, Vec<Hand>> {
    let (s, hands) = separated_list1(newline, hand)(s)?;
    Ok((s, hands))
}
```

I probably overdid this. One nice thing that we get for free though is `#[derive(PartialOrd, Ord)]` on `Card`. This will later to the lexicographic ordering for free. 

### Solving the Problem

Okay, we have *almost* everything we need, but we still want to be able to order `Hand` as well as `Card`. We can't just do the trivial `derive` this time, unless we implement a `enum HandType` with `Ord` (which we certainly could do). But instead, let's implement `Ord` (and `PartialOrd`) on `Hand`:

```rust
impl Hand {
    fn counts(&self) -> Vec<usize> {
        let mut counts: HashMap<Card, usize> =
            self.cards
                .into_iter()
                .fold(HashMap::new(), |mut counts, c| {
                    *counts.entry(c).or_default() += 1;
                    counts
                });

        let mut counts = counts.values().cloned().collect::<Vec<_>>();
        counts.sort();
        counts.reverse();
        counts
    }
}

impl Ord for Hand {
    fn cmp(&self, other: &Self) -> Ordering {
        let self_counts = self.counts();
        let other_counts = other.counts();

        // Counts are sorted in descending order, so we can compare them directly
        // IE five of a kind is <5>, four of a is <4, 1>, full house is <3, 2>, three of a is <3, 1, 1> etc
        // If two counts are the same, compare the cards lexicographically (using Ord on Card)
        if self_counts == other_counts {
            self.cards.cmp(&other.cards)
        } else {
            self_counts.cmp(&other_counts)
        }
    }

    fn max(self, other: Self) -> Self {...}
    fn min(self, other: Self) -> Self {...}
    fn clamp(self, _min: Self, _max: Self) -> Self {...}
}

impl PartialOrd for Hand {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
```

Okay, there's a bit to unfold (heh) there. What I want to do is produce a list of counts of cards, ordered by the number in the set descending. So `AKAAA` should be `<4, 1>` etc. To do that, we can use a `fold` to build a `HashMap` of `Card` to `count`. 

Then, get just the counts (we don't actually care what kind of card it is for this ordering) and collect them into a `Vec`. This is nice because `Vec` is already `Ord` (if it's elements are) and it's lexicographic (I seem to be saying that word a lot). 

So we just have to compare `self_counts` and `other_counts`. If they're the same, compare `self.cards` and `other.cards`. 

One bit of weirdness is that we have to implement both `Ord` and `PartialOrd`. If you do a custom implementation of one, it (for some reason) can't derive the other automatically from it? Or at least `cargo clippy` didn't want me to let it. I did just leave `max`, `min`, and `clamp` as `unimplemented!` though. We don't need them for this. 

And ... that's it!

```rust

fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, mut hands) = parse::hands(&input).unwrap();
    assert_eq!(s.trim(), "");

    hands.sort();

    let result = hands
        .iter()
        .enumerate()
        .map(|(i, h)| (i + 1) * h.bid as usize)
        .sum::<usize>();

    println!("{result}");
    Ok(())
}
```

Parse the `hands`, `sort` them (why we did all the `Ord` things), and apply the scoring. 

## Part 2

> Treat `J` as Jokers rather than as Jacks. For the purposes of hand type (four of a kind etc), treat jokers as whatever card would score the hand highest. For the purposes of tie-breaking, treat it as the lowest value. 

Well that's neat. Especially because they go opposite ways. So to start off, we'll expand the types and parsing with Jokers:

```rust
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Copy, Clone, Hash)]
pub enum Card {
    Joker,
    Two,
    // ...
}

impl From<char> for Card {
    fn from(c: char) -> Self {
        match c {
            '*' => Card::Joker,
            // ...
        }
    }
}
```

By adding `Joker` first to `Card`, it will automatically be sorted as the lowest value. By parsing `*` as a `Joker` rather than `J`, this functionality works for both part 1 and part 2 (we will have to rewrite the input though, we'll come back to that). 

And then we have to add a bit of code to `counts`:

```rust
impl Hand {
    fn counts(&self) -> Vec<usize> {
        let mut counts: HashMap<Card, usize> =
            self.cards
                .into_iter()
                .fold(HashMap::new(), |mut counts, c| {
                    *counts.entry(c).or_default() += 1;
                    counts
                });

        // Special case for part 2, if we have any jokers assign them to the otherwise largest group
        // For 5 jokers, treat as 5 Aces (but this won't actually matter)
        if counts.contains_key(&Card::Joker) {
            let best_type = counts.iter().fold(Card::Ace, |best_type, (&k, &v)| {
                // Update if non-joker with more than current
                // If there's nothing but jokers, replace with Aces
                if k != Card::Joker && v > *(counts.get(&best_type).unwrap_or(&0)) {
                    k
                } else {
                    best_type
                }
            });

            *counts.entry(best_type).or_default() += counts[&Card::Joker];
            counts.remove(&Card::Joker);
        }

        let mut counts = counts.values().cloned().collect::<Vec<_>>();
        counts.sort();
        counts.reverse();
        counts
    }
}
```

There are a few interesting edge cases to deal with there:

* No `Jokers` (we just skip the block)
* All `Jokers` (treat them all as `Aces`, although as noted this won't matter since 5 of a kind is 5 of a kind)
* 1-4 jokers: go through all the types and find the one with the most entries; add the Jokers to this and remove them (so we don't end up with more than 5 cards)

You can go through all the types to determine this for yourself, but this works because of how the `Ord` on `Hand` works. The most common count is always the one that will be most improved by adding `Jokers` to it. 

It's not the prettiest code (`.unwrap_or(&0)` remains a weird necessity), but it's functional. Nothing changes in the `Ord` implementation, and there's just one extra line in the solution:

```rust
let input = input.replace('J', "*");
```

And that's it. We have part 2. 

## Performance

```bash
$ just time 7 1

hyperfine 'just run 7 1'
Benchmark 1: just run 7 1
  Time (mean ± σ):      85.3 ms ±   5.9 ms    [User: 33.4 ms, System: 11.2 ms]
  Range (min … max):    80.8 ms … 105.2 ms    27 runs

$ just time 7 2

hyperfine 'just run 7 2'
Benchmark 1: just run 7 2
  Time (mean ± σ):      87.6 ms ±   5.2 ms    [User: 34.5 ms, System: 12.1 ms]
  Range (min … max):    82.5 ms … 107.4 ms    27 runs
```

Plenty quick. Nothing much more to do here. 