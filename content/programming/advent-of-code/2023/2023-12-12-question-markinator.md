---
title: "AoC 2023 Day 12: Question Markinator"
date: 2023-12-12 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 12: Hot Springs](https://adventofcode.com/2023/day/12)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day12) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a sequence of `#.?` as on, off, and unknown and a sequence of group sizes, determine how many possible arrangements there are that match the given groups. 
>
> More specifically, if you have `???.## 1,2` you need a single `#` and a set of two `##`, there are three possibilities: `#...###`, `.#..###`, and `..#.###`. 
 
<!--more-->

### Types and Parsing

Okay, let's represent this thing:

```rust
#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub enum Condition {
    Operational,
    Damaged,
    Unknown,
}
impl Condition {
    pub fn is_known(&self) -> bool {
        !matches!(self, Condition::Unknown)
    }
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub struct Spring {
    pub conditions: Vec<Condition>,
    pub groups: Vec<u64>,
}

fn condition(s: &str) -> IResult<&str, Condition> {
    alt((
        map(tag("#"), |_| Condition::Operational),
        map(tag("."), |_| Condition::Damaged),
        map(tag("?"), |_| Condition::Unknown),
    ))(s)
}

fn spring(s: &str) -> IResult<&str, Spring> {
    let (s, conditions) = many1(condition)(s)?;
    let (s, _) = space1(s)?;
    let (s, groups) = separated_list1(char(','), complete::u64)(s)?;

    Ok((s, Spring { conditions, groups }))
}

pub fn springs(s: &str) -> IResult<&str, Vec<Spring>> {
    separated_list1(line_ending, spring)(s)
}
```

Pretty straight forward. 

Originally, I had just `Operational` and `Damaged` with `Option` (`None`) to represent unknown parts, but really, it just the made the code more confusing, so I changed that before even version 1. 

### Solution

But the really interesting part is the solution:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, springs) = parse::springs(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = springs
        .iter()
        .map(|s| {
            use Condition::*;

            let mut possibles = 0;
            let mut queue = Vec::new();
            queue.push(s.conditions.clone());

            while let Some(current) = queue.pop() {
                // If there are no unknown components, score it
                if current.iter().all(|c| c.is_known()) {
                    let groups = current
                        .iter()
                        .chain(std::iter::once(&Damaged))
                        .fold(
                            (Damaged, 0, vec![]),
                            |(previous, current_length, mut lengths), current| match (
                                previous, current,
                            ) {
                                (Operational, Operational) => {
                                    (Operational, current_length + 1, lengths)
                                }
                                (Operational, Damaged) => {
                                    lengths.push(current_length);
                                    (Damaged, 0, lengths)
                                }
                                (Damaged, Operational) => {
                                    (Operational, 1, lengths)
                                }
                                (Damaged, Damaged) => {
                                    (Damaged, 0, lengths)
                                }
                                _ => panic!("Invalid state, previous: {:?}, current: {:?}", previous, current)
                            },
                        )
                        .2;

                    if groups == s.groups {
                        possibles += 1;
                    }
                } else {
                    // Otherwise, queue one in with each possibility
                    for (i, condition) in current.iter().enumerate() {
                        if !condition.is_known() {
                            let mut next = current.clone();
                            next[i] = Operational;
                            queue.push(next);

                            let mut next = current.clone();
                            next[i] = Damaged;
                            queue.push(next);
                            break;
                        }
                    }
                }
            }

            possibles
        })
        .sum::<u64>();

    println!("{result}");
    Ok(())
}
```

Yeah, okay. That's a bit ugly. Essentially, we're going to solve the problem by:

1. Initialize a stack of potential solutions with the initial state
2. For each solution:
   1. If it has at least one `?` left, push a two new copies with it set to either `.` or `#`
   2. If it has no `?` left, score it (it either matches the target groups or not)

The most interesting part is probably the `fold`. That's calculating sequential groups by keeping track of the previous character (so you know if you change from `.#` or vice versa) and the current count and `match (previous, current)` against them. 

It's not terrible code... but I can already guess that this is going to blow up in part 2. 

### Cleaning up

Speaking of terrible, we can move some of this functionality to `impl Spring` and make things I think a little cleaner. 

First, a helper method that will wrap up that `fold` from before (although it's a `for` now) into a single method:

```rust
impl Spring {
    pub fn current_groups(&self) -> (Vec<u64>, u64) {
        use Condition::*;

        let mut groups = vec![];
        let mut group: u64 = 0;
        let mut previous = Condition::Damaged;

        for current in self.conditions.iter().chain(std::iter::once(&Damaged)) {
            match (previous, current) {
                // Continuing this group
                (Operational, Operational) => group += 1,
                // Ending a group
                (Operational, Damaged) => {
                    groups.push(group);
                    group = 0;
                }
                // Starting a new group
                (Damaged, Operational) => group = 1,
                // Currently not in a group
                (Damaged, Damaged) => {}
                // If we hit an unknown, bail early with the current groups
                (_, Unknown) => break,
                _ => panic!("Invalid state"),
            }
            previous = *current;
        }

        (groups, group)
    }
}
```

This one is slightly different. Rather than matching the entire sequence only, this one will handle partial sequences, up until you get to the first `?`. It will then also return two things: any groups completed + the length of the last currently incomplete group.

This then lets us write some more helpers:

```rust
impl Spring {
    pub fn is_valid(&self) -> bool {
        let (groups, next_group) = self.current_groups();

        if !self.groups.starts_with(&groups) {
            return false;
        }

        if groups.len() < self.groups.len()
            && next_group > 0
            && self.groups[groups.len()] < next_group
        {
            return false;
        }

        true
    }

    pub fn is_known(&self) -> bool {
        self.conditions.iter().all(|c| c.is_known())
    }

    pub fn is_correct(&self) -> bool {
        self.is_known() && self.groups == self.current_groups().0
    }
}
```

In this case, `is_valid` will tell us if it's *possible* that the current solution is still valid, based only on the section up to the first `?` (using `current_groups`). The second `if` with three clauses makes sure that you don't have to generate all lengths of final groups with a terminating `.` before bailing out. As soon as you've counted up more than the `next_group`, you're already invalid.

After that, `is_known` defines the end case (all values set) and `is_correct` verifies that you have exactly the correct solution. 

With all these, we can have a cleaner (if not that much shorter) part 1:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (s, springs) = parse::springs(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = springs
        .iter()
        .map(|s| {
            use Condition::*;

            let mut possibles = 0;
            let mut queue = VecDeque::new();
            queue.push_back(s.clone());

            while let Some(current) = queue.pop_front() {
                // If the current state is impossible, skip it
                if !current.is_valid() {
                    // println!("{current} is invalid");
                    continue;
                }

                // If it is possible and completely known, score it
                if current.is_correct() {
                    // println!("{current} is scoring");
                    possibles += 1;
                    continue;
                }

                // Otherwise, queue one in with each possibility
                for (i, condition) in current.conditions.iter().enumerate() {
                    if !condition.is_known() {
                        let mut next = current.clone();
                        next.conditions[i] = Operational;
                        queue.push_back(next);

                        let mut next = current.clone();
                        next.conditions[i] = Damaged;
                        queue.push_back(next);
                        break;
                    }
                }
            }

            possibles
        })
        .sum::<u64>();

    println!("{result}");
    Ok(())
}
```

It's significantly faster too (roughly ~15x), although that's more due to the `is_valid` bailing out early than the cleaner code. 

Okay. Let's see what tricks they have for us. 

## Part 2

> Repeat each input sequence 5x. Delimit the first inputs by an extra `?` and the second by the necessary `,`. So `#.? 1,1` becomes `#.??#.??#.??#.??#.? 1,1,1,1,1,1,1,1,1,1`.

Well. That certainly makes things longer. 

Rewriting the input isn't too bad:

```rust
fn drep(s: &str, d: &str, n: usize) -> String {
    std::iter::repeat(s).take(n).collect::<Vec<_>>().join(d)
}

let input = input
    .lines()
    .map(|line| {
        let parts = line.split_once(' ').unwrap();
        drep(parts.0, "?", 5) + " " + &drep(parts.1, ",", 5)
    })
    .collect::<Vec<_>>()
    .join("\n");
println!("{input}");
```

### (Almost) Brute Force

But... there's no way this is going to run in anyway at all fast. 

```rust
just run 12 2-brute

cat data/$(printf "%02d" 12).txt | cargo run --release -p day$(printf "%02d" 12) --bin part2-brute
   Compiling day12 v0.1.0 (/Users/jp/Projects/advent-of-code/2023/solutions/day12)
    Finished release [optimized] target(s) in 0.18s
     Running `target/release/part2-brute`
0, q=0, p=0: ??#??#??##.#???????#??#??##.#???????#??#??##.#???????#??#??##.#???????#??#??##.#????
[solutions/day12/src/bin/part2-brute.rs:72] possibles = 512
0, q=0, p=0: .#?#.???#?.???.#?#.???#?.???.#?#.???#?.???.#?#.???#?.???.#?#.???#?.??
[solutions/day12/src/bin/part2-brute.rs:72] possibles = 5184
0, q=0, p=0: #???.#???#?.?.??.??#???.#???#?.?.??.??#???.#???#?.?.??.??#???.#???#?.?.??.??#???.#???#?.?.??.?
1000000, q=32, p=29160: ##.#.#####..#.#...##.#..#####.....#...#....##..#.......#####..#.#.##........#....#####..#.#?.?
[solutions/day12/src/bin/part2-brute.rs:72] possibles = 32805
0, q=0, p=0: ??#??#???????????#??#???????????#??#???????????#??#???????????#??#????????
1000000, q=44, p=3853: ..#..#####.......#..#....#####..#..#...........#####....#.#...#####.#..#.?
2000000, q=34, p=66884: ..#..#####.......#..#.#####..#..#.#####.#..#..#####.#.........##?#????????
3000000, q=38, p=132766: ..#..#####.....#.#..#####...#.#.#####....#..#..#####..#.....#.#####.#....?
4000000, q=40, p=198154: ..#..#####.....#.#..#####..#.#.#####..#.....#..#####..#..#...#####........
5000000, q=32, p=263202: ..#..#####.....#.#..#####.#..#.#####..#..#....#####....#..#.#.#??#????????
6000000, q=36, p=327133: ..#..#####.....#.#.#####.....#..#.#####..#..#.#####...#....#.#####.#..###.
7000000, q=34, p=393297: ..#..#####.....#.#.#####...#.#..#####..#..#.#####.#......#....#####.#?????
8000000, q=36, p=458305: ..#..#####.....#.#.#####..#..#..#####.#....#...#####...#.#...#####....##??
9000000, q=38, p=522607: ..#..#####.....#.#.#####.#......#..#####.#.#..#####...#...#..#####.....#.#
10000000, q=28, p=587737: ..#..#####.....#.#.#####.#..#...#####...#.#...#####....#??????#??#????????
```

That's a whole mess of output. The import part is that each of those lines at the bottom is going through 1 million possible cases and we already have a roughly 6% success rate.  

And that's *with* the `is_valid` optimization.

We're going to need something better.

### Caching

Okay, what I expect we're going to want is [[wiki:dynamic programming]]() / [[wiki:caching]]() / [[wiki:memoization]](). 

We want to take the original problem and somehow break it down to one or more smaller problems. For each of those smaller problems, continue to break it down. And then whenever (for a smaller problem), we get an answer, assume that another of those very very very many branches is going to ask the same (sub)question, so write it down. 

In essence, this:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    fn drep(s: &str, d: &str, n: usize) -> String {
        std::iter::repeat(s).take(n).collect::<Vec<_>>().join(d)
    }

    let input = input
        .lines()
        .map(|line| {
            let parts = line.split_once(' ').unwrap();
            drep(parts.0, "?", 5) + " " + &drep(parts.1, ",", 5)
        })
        .collect::<Vec<_>>()
        .join("\n");

    let result = input
        .lines()
        .map(|line| {
            let parts = line.split_once(' ').unwrap();
            let conditions = parts.0.as_bytes();
            let groups = parts
                .1
                .split(',')
                .map(|s| s.parse().unwrap())
                .collect::<Vec<_>>();

            Solver::new().check(conditions, b'.', b'.', &groups, 0)
        })
        .sum::<u128>();

    println!("{result}");
    Ok(())
}
```

Yeah, yeah, that's definitely a [how to draw an owl](https://knowyourmeme.com/memes/how-to-draw-an-owl) moment, but hang with me. The `Solver::new().check` is going to recursively do the work. 

I'm not messing with types here, since I want to only use pointers into that original string slice of input (I could make a single processed slice of my own types, we'll [come back to that](#rewriting-it-with-types)). 

But for now, what in the world does `Solver` look like?

```rust
type Key<'a> = (&'a [u8], u8, u8, &'a [u64], u64);
struct Solver<'a> {
    cache: FxHashMap<Key<'a>, u128>,
}

impl<'a> Solver<'a> {
    fn new() -> Self {
        Self {
            cache: FxHashMap::default(),
        }
    }

    fn check(
        &mut self,
        s: &'a [u8],       // The remaining input string after current
        curr: u8,          // The current character to check
        prev: u8,          // The previous character to check
        groups: &'a [u64], // The remaining groups to match
        count: u64,        // The size of the current group
    ) -> u128 {
        let key = (s, curr, prev, groups, count);

        if let Some(value) = self.cache.get(&key) {
            return *value;
        }

        let result = {
            if groups.is_empty() {
                // Base case, we have no more groups to go
                // Everything else must not be #
                if curr == b'#' || s.iter().any(|c| *c == b'#') {
                    0
                } else {
                    1
                }
                // From here on out, we know groups is not empty
            } else if curr == b'?' {
                // Current is unknown, try both cases (without advancing s!)
                let if_d = self.check(s, b'.', prev, groups, count);
                let if_o = self.check(s, b'#', prev, groups, count);
                if_d + if_o
            } else if s.is_empty() {
                // This block seems wrong, but I need it to have curr and prev work with ?
                // We have no more input, check the last current
                // We have at least one group at this point
                if curr == b'#' {
                    // If the last current is operational, we need to match the last group
                    if groups.len() == 1 && count + 1 == groups[0] {
                        1
                    } else {
                        0
                    }
                } else if curr == b'.' {
                    // If we came from operational check the last group
                    if groups.len() == 1 && count == groups[0] {
                        1
                    } else {
                        0
                    }
                } else {
                    panic!("got something weird on empty input: {curr}")
                }
            } else if curr == b'#' {
                // Current is operational
                if prev == b'.' {
                    // After damaged, start a new group
                    self.check(&s[1..], s[0], curr, groups, 1)
                } else if prev == b'#' {
                    // After another operational, continue group
                    self.check(&s[1..], s[0], curr, groups, count + 1)
                } else {
                    panic!("got # after something weird: {prev}")
                }
            } else if curr == b'.' {
                // Current is damaged
                if prev == b'.' {
                    // After another damaged, nothing happens
                    self.check(&s[1..], s[0], curr, groups, 0)
                } else if prev == b'#' {
                    // After operational, finish the current group
                    // If the size doesn't match, this branch is immediately invalid
                    if count == groups[0] {
                        self.check(&s[1..], s[0], curr, &groups[1..], 0)
                    } else {
                        0
                    }
                } else {
                    panic!("got . after something weird: {prev}")
                }
            } else {
                panic!("got something weird: {curr}")
            }
        };

        // dbg!(result);

        self.cache.insert(key, result);
        result
    }
}
```

It could certainly be longer... and it's at least well documented? 

The main thing to start with is the signature:

```rust
fn check(
    &mut self,
    s: &'a [u8],       // The remaining input string after current
    curr: u8,          // The current character to check
    prev: u8,          // The previous character to check
    groups: &'a [u64], // The remaining groups to match
    count: u64,        // The size of the current group
) 
```

As mentioned, `s` is future input. `curr` is the current input--roughly `s[-1]` if that worked--and `prev` is the previous one--`s[-2]`--as we dealt with before. `groups` is the groups we haven't matched yet and `count` is the length of the current group. 

So we end up with a whole bunch of cases:

* If we go from (`prev`) a damaged `.` section...
  * to a operational `#` section: start counting a new group
  * to another damaged section: nothing changes (group count is 0)
* If we go from a operational section...
  * to another operational section: increment the current group
  * to a damaged section: end the current group
    * If it matches the next (first) value of `groups`: we're done with that group, move on
    * Otherwise, this solution is not possibly valid and we can bail out early!

But there are also a bunch of extra cases:

* If we hit an unknown `?` section: try both. This changes `curr` but does *not* change `s` or anything else. This is actually the exact reason why we have `curr`: because we don't want to (and can't) mutate `s[0]`
* If we run out of groups: If the rest of the input has only `.` or `?` (which can be `.`), this is fine. Count it as a solution. But even one `#` and we're completely invalid.
* If we run out of input, we still have to deal with the last `curr` character.

It took a little while to finagle that all out, but when I did:

```bash
$ just time 12 2

hyperfine --warmup 3 'just run 12 2'
Benchmark 1: just run 12 2
  Time (mean ± σ):      1.196 s ±  0.053 s    [User: 1.052 s, System: 0.046 s]
  Range (min … max):    1.160 s …  1.337 s    10 runs
```

Oh, that's not bad at all! I think we can do a bit better though...

### A choice of map

You might have noticed that ... I'm not actually using `HashMap`. Instead, I'm using [`fxhash::HashMap`](https://docs.rs/fxhash/latest/fxhash/). The built in hashing function in Rust is designed to be cryptographically secure, but that comes at a performance cost. Granted, it's still far faster in many cases than *not* using a map, but let's try the other options:

```bash
# BTreeMap

$ just time 12 2

hyperfine --warmup 3 'just run 12 2'
Benchmark 1: just run 12 2
  Time (mean ± σ):      1.460 s ±  0.260 s    [User: 1.322 s, System: 0.037 s]
  Range (min … max):    1.155 s …  1.761 s    10 runs

# fxhash::HashMap

$ just time 12 2

hyperfine --warmup 3 'just run 12 2'
Benchmark 1: just run 12 2
  Time (mean ± σ):     607.8 ms ±   5.6 ms    [User: 492.9 ms, System: 40.5 ms]
  Range (min … max):   595.6 ms … 615.1 ms    10 runs
```

`BTreeMap` works by sorting the data rather than hashing it, but often has `log(n)` runtimes rather than `n` that we want. `fxhash` instead uses a much faster hashing algorithm that doesn't worry about attacks. It's ... pretty impressive. Roughly a 2x speedup and we're under a second!

### Rewriting it with types

Okay, we got it working... but it does bother me a bit that we're not using those types. We should be able to use `&[Condition]` instead of `&[u8]` without much problem, right? 

```rust
type Key<'a> = (&'a [Condition], Condition, Condition, &'a [u64], u64);
struct Solver<'a> {
    cache: FxHashMap<Key<'a>, u128>,
}

impl<'a> Solver<'a> {
    fn new() -> Self {
        Self {
            cache: FxHashMap::default(),
        }
    }

    fn check(
        &mut self,
        s: &'a [Condition], // The remaining input string after current
        curr: Condition,    // The current character to check
        prev: Condition,    // The previous character to check
        groups: &'a [u64],  // The remaining groups to match
        count: u64,         // The size of the current group
    ) -> u128 {
        use Condition::*;
        let key = (s, curr, prev, groups, count);

        if let Some(value) = self.cache.get(&key) {
            return *value;
        }

        let result = {
            if groups.is_empty() {
                // Base case, we have no more groups to go
                // Everything else must not be #
                if curr == Operational || s.iter().any(|c| *c == Operational) {
                    0
                } else {
                    1
                }
                // From here on out, we know groups is not empty
            } else if curr == Unknown {
                // Current is unknown, try both cases (without advancing s!)
                let if_d = self.check(s, Damaged, prev, groups, count);
                let if_o = self.check(s, Operational, prev, groups, count);
                if_d + if_o
            } else if s.is_empty() {
                // This block seems wrong, but I need it to have curr and prev work with ?
                // We have no more input, check the last current
                // We have at least one group at this point
                if curr == Operational {
                    // If the last current is operational, we need to match the last group
                    if groups.len() == 1 && count + 1 == groups[0] {
                        1
                    } else {
                        0
                    }
                } else if curr == Damaged {
                    // If we came from operational check the last group
                    if groups.len() == 1 && count == groups[0] {
                        1
                    } else {
                        0
                    }
                } else {
                    panic!("got something weird on empty input: {curr:?}")
                }
            } else if curr == Operational {
                // Current is operational
                if prev == Damaged {
                    // After damaged, start a new group
                    self.check(&s[1..], s[0], curr, groups, 1)
                } else if prev == Operational {
                    // After another operational, continue group
                    self.check(&s[1..], s[0], curr, groups, count + 1)
                } else {
                    panic!("got # after something weird: {prev:?}")
                }
            } else if curr == Damaged {
                // Current is damaged
                if prev == Damaged {
                    // After another damaged, nothing happens
                    self.check(&s[1..], s[0], curr, groups, 0)
                } else if prev == Operational {
                    // After operational, finish the current group
                    // If the size doesn't match, this branch is immediately invalid
                    if count == groups[0] {
                        self.check(&s[1..], s[0], curr, &groups[1..], 0)
                    } else {
                        0
                    }
                } else {
                    panic!("got . after something weird: {prev:?}")
                }
            } else {
                panic!("got something weird: {curr:?}")
            }
        };

        // dbg!(result);

        self.cache.insert(key, result);
        result
    }
}

// #[aoc_test("data/test/12.txt", "21")]
// #[aoc_test("data/12.txt", "7025")]
fn main() -> Result<()> {
    use Condition::*;

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (s, springs) = parse::springs(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = springs
        .iter()
        .map(|spring| Spring {
            conditions: (spring
                .conditions
                .clone()
                .into_iter()
                .chain(std::iter::once(Unknown))
                .collect::<Vec<_>>())
            .into_iter()
            .cycle()
            .take(spring.conditions.len() * 5 + 4)
            .collect::<Vec<_>>(),
            groups: spring
                .groups
                .clone()
                .into_iter()
                .cycle()
                .take(spring.groups.len() * 5)
                .collect::<Vec<_>>(),
        })
        .map(|spring| Solver::new().check(&spring.conditions, Damaged, Damaged, &spring.groups, 0))
        .sum::<u128>();

    println!("{result}");
    Ok(())
}
```

Yes actually. 

And it's not that much longer code and (I could argue), it's a bit easier to read. 

The new 5x codes are a bit weird. I orignally had `.into_iter().chain(...).cycle()`, but that actually doesn't do at all what you want, it cycles the chained iterator (many unknowns), not the whole thing. This the extra parens. 

So... does it perform well? 

```bash
$ just time 12 2-typed

hyperfine --warmup 3 'just run 12 2-typed'
Benchmark 1: just run 12 2-typed
  Time (mean ± σ):     893.5 ms ±   8.5 ms    [User: 764.8 ms, System: 51.5 ms]
  Range (min … max):   878.1 ms … 909.4 ms    10 runs
```

That's actually really close (and still under a second!). 

I'm curious what the difference is... but not enough to mess with it right now. Perhaps I'll come back to this later in the month. We shall see!

## Performance

We've already seen these, but...

```bash
$ just time 12 1

hyperfine --warmup 3 'just run 12 1'
Benchmark 1: just run 12 1
  Time (mean ± σ):     120.3 ms ±   5.2 ms    [User: 56.9 ms, System: 13.4 ms]
  Range (min … max):   112.1 ms … 136.6 ms    24 runs

$ just time 12 2

hyperfine --warmup 3 'just run 12 2'
Benchmark 1: just run 12 2
  Time (mean ± σ):     654.8 ms ±   6.2 ms    [User: 531.8 ms, System: 51.0 ms]
  Range (min … max):   648.3 ms … 667.6 ms    10 runs
```

Not bad. Especially given the who knows how much longer we had it running for before. 