---
title: "AoC 2022 Day 4: Overlapinator"
date: 2022-12-04 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Camp Cleanup](https://adventofcode.com/2022/day/4)

#### **Part 1:** Given a list of pairs of spans (of the form a-b,x-y) count how many spans have one span entirely contained within the other.

<!--more-->

Fair enough. Let's make a `Span`:

```rust
struct Span {
    min: isize,
    max: isize,
}

impl Span {
    fn new(s: &str) -> Span {
        let (min, max) = s.split_at(s.find("-").expect("missing dash in span"));

        Span {
            min: min.parse::<isize>().expect("min is not an integer"),
            max: max.strip_prefix("-").expect("malformed prefix, missing dash").parse::<isize>().expect("max is not an integer"),
        }
    }

    fn contains(&self, other: &Span) -> bool {
        self.min <= other.min && self.max >= other.max
    }
}

fn parse(lines: &Vec<String>) -> Vec<(Span, Span)> {
    let mut result = Vec::new();

    for line in lines {
        let (left, right) = line.split_at(line.find(",").expect("missing comma in line"));
        result.push((Span::new(left), Span::new(right.strip_prefix(",").expect("malformed prefix, missing comma"))))
    }

    result
}
```

This time I'm going to use `split_at` and `find` instead of `split`, since I know there will always be exactly two values (first separated by a comma and then a dash within the span). That should be enough to parse everything. 

So far as `contains`, it's easy enough since they're ordered. For one `Span` to contain another, it's `min` must be greater and it's `max` smaller (inclusive in both cases). This gives us the completely disjoin cases, since one will be true and the other false in all of those. 

Now to count them, a nice `filter` and `len`:

```rust
fn part1(filename: &Path) -> String {
    let span_pairs = parse(&read_lines(filename));

    let containing: Vec<&(Span, Span)> = span_pairs.iter().filter(
        |pair| pair.0.contains(&pair.1) || pair.1.contains(&pair.0)
    ).collect();

    containing.len().to_string()
}
```

That works well enough, but one downside is that we're allocating memory for the collected results when... we don't really care what the values are. Just that they exist. You can't directly use `len` on an iterator (such as a Filter)... but you can use `count`!

```rust
fn part1(filename: &Path) -> String {
    parse(&read_lines(filename)).iter().filter(
        |pair| pair.0.contains(&pair.1) || pair.1.contains(&pair.0)
    ).count().to_string()
}
```

That's pretty minimal. Is it actually more or less readable? I think it's pretty decent at least. 

#### **Part 2:** Instead, count how many spans have one overlapping the other at all. 

Okay, expand the implementation of `Span`:

```rust
impl Span {
    fn overlaps(&self, other: &Span) -> bool {
        (self.min >= other.min && self.min <= other.max) 
            || (self.max >= other.min && self.max <= other.max)
            || (other.max >= self.min && other.max <= self.max)
            || (other.max >= self.min && other.max <= self.max)
    }
}
```

A bit messier, but it needs to be to deal properly with the single value edge cases (`6-6`). And it'll all short circuit nicely if they don't overlap, so it works. The `part2` itself just subs out the function:

```rust
fn part2(filename: &Path) -> String {
    parse(&read_lines(filename)).iter().filter(
        |pair| pair.0.overlaps(&pair.1)
    ).count().to_string()
}
```

#### Performance

Quick. 

```rust
$ ./target/release/04-overlapinator 1 data/04.txt

466
took 442.458µs

$ ./target/release/04-overlapinator 2 data/04.txt

865
took 362.166µs
```

We're still really not doing anything outside of {{<inline-latex "O(n)">}}.