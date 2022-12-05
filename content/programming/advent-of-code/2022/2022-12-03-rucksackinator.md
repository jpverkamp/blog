---
title: "AoC 2022 Day 3: Rucksackinator"
date: 2022-12-03 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Rucksack Reorganization](https://adventofcode.com/2022/day/3)

#### **Part 1:** Take a list of characters. For each line, split the line exactly in half and find the one character that's in both halves. Assign a-z to values 1-26 and A-Z to 27-52. Sum these values. 

<!--more-->

This one abstracted... oddly. 

```rust
#[derive(Debug)]
struct Rucksack {
    all: HashSet<char>,
    left: HashSet<char>,
    right: HashSet<char>,
}

impl Rucksack {
    fn new(items: String) -> Rucksack {
        let all = items.chars().collect();

        let half = items.len() / 2;
        let left = items.chars().take(half).collect();
        let right = items.chars().skip(half).collect();

        Rucksack { all, left, right }
    }
}

fn rucksack_priority(c: &char) -> u32 {
    match c {
        'a'..='z' => (*c as u32) - ('a' as u32) + 1,
        'A'..='Z' => (*c as u32) - ('A' as u32) + 27,
        _ => panic!("unknown rucksack character: {:?}", c)
    }
}
```

It makes enough sense to make the `Rucksack` out of two sets since we don't care if values are unique in either half, just if they're unique within the entire rucksack. 

The real mess of the function comes with applying a bunch of filters and set operations in sequence in Rust:

```rust
fn part1(filename: &Path) -> String {
    let lines: Vec<String> = read_lines(filename);

    let rucksacks: Vec<Rucksack> = lines.into_iter().map(Rucksack::new).collect();

    let uniques: Vec<Vec<&char>> = rucksacks.iter().map(
        |r| r.left.intersection(&r.right).collect()
    ).collect();

    let priorities: Vec<Vec<u32>> = uniques.into_iter().map(
        |ls| ls.into_iter().map(rucksack_priority).collect()
    ).collect();

    priorities.into_iter().map(|ls| ls.iter().sum::<u32>()).sum::<u32>().to_string()
}
```

I'm not sure what to think about that. The code is clean enough I suppose, but having to specify all of the types I feel is somewhat counterintuitive. 

It does work well enough though. 

```bash
$ ./target/release/03-rucksackinator 1 data/03.txt

7845
took 2.813541ms
```

#### **Part 2:** Instead, group each set of 3 inputs. Find the one character that occurs in each of the three lines of each group. Score as before. 

This isn't actually *that* much different:

```rust

fn part2(filename: &Path) -> String {
    let lines: Vec<String> = read_lines(filename);

    let rucksacks: Vec<Rucksack> = lines.into_iter().map(Rucksack::new).collect();

    let groups: Vec<&[Rucksack]> = rucksacks.chunks(3).collect();

    let uniques: Vec<HashSet<char>> = groups.into_iter().map(
        |g| g[0].all
            .intersection(&g[1].all).copied().collect::<HashSet<char>>()
            .intersection(&g[2].all).copied().collect()
    ).collect();

    let priorities: Vec<Vec<u32>> = uniques.into_iter().map(
        |ls| ls.iter().map(rucksack_priority).collect()
    ).collect();

    priorities.into_iter().map(|ls| ls.iter().sum::<u32>()).sum::<u32>().to_string()
}
```

Mostly, instead of going through each, we have to get `chunks` first, then intersect the 3 `.all` sets from each chunk. I'm not a fan of that chaining. Is there a better way to do it? 

Still fast though:

```bash
$ ./target/release/03-rucksackinator 2 data/03.txt

2790
took 2.230958ms
```
