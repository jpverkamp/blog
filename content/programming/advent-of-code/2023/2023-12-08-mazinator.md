---
title: "AoC 2023 Day 8: Mazinator"
date: 2023-12-08 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 8: Haunted Wasteland](https://adventofcode.com/2023/day/8)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day08) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a (repeated) sequence of moves (`L` for left and `R` for right) and a directed graph where each node has two neighbors (left and right), count how many total steps it takes to get from the node `AAA` to the node `ZZZ`. The sequence of moves can (and will) need to repeat. 

<!--more-->

### Types and Parsing

I think the only really interesting part in this one was the use of `Label` as an alias of `[char; 3]`:

```rust
#[derive(Debug, Clone, Copy)]
pub enum Move {
    Left,
    Right,
}

pub type Label = [char; 3];

#[derive(Debug, Clone, Copy)]
pub struct Neighbors {
    pub left: Label,
    pub right: Label,
}

#[derive(Debug, Clone)]
pub struct Simulation {
    pub moves: Vec<Move>,
    pub neighbors: BTreeMap<Label, Neighbors>,
}
```

We probably could have also used `&str` there, but I figure that copying (always) 3 chars is probably pretty fast? If allocation becomes an issue, we can fix this. 

```rust
fn moves(s: &str) -> IResult<&str, Vec<Move>> {
    let (s, moves) = many1(alt((
        map(tag("L"), |_| Move::Left),
        map(tag("R"), |_| Move::Right),
    )))(s)?;
    Ok((s, moves))
}

fn label(s: &str) -> IResult<&str, Label> {
    let (s, label) = tuple((anychar, anychar, anychar))(s)?;
    Ok((s, label.into()))
}

fn mapping(s: &str) -> IResult<&str, (Label, Neighbors)> {
    let (s, (label, left, right)) = tuple((
        label,
        preceded(tag(" = ("), label),
        terminated(preceded(tag(", "), label), tag(")")),
    ))(s)?;

    Ok((s, (label, Neighbors { left, right })))
}

pub fn simulation(s: &str) -> IResult<&str, Simulation> {
    let (s, moves) = moves(s)?;
    let (s, _) = newline(s)?;
    let (s, _) = newline(s)?;
    let (s, neighbors) = separated_list1(newline, mapping)(s)?;
    Ok((
        s,
        Simulation {
            moves,
            neighbors: neighbors.into_iter().collect(),
        },
    ))
}
```

### Solution

Let's start with the code:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, ref simulation) = parse::simulation(&input).unwrap();
    assert_eq!(s.trim(), "");

    let mut current: Label = ['A', 'A', 'A'];
    let target: Label = ['Z', 'Z', 'Z'];
    let mut result = 0;

    for m in simulation.moves.iter().cycle() {
        result += 1;

        current = match m {
            Move::Left => simulation.neighbors[&current].left,
            Move::Right => simulation.neighbors[&current].right,
        };

        if current == target {
            break;
        }
    }

    println!("{result}");
    Ok(())
}
```

Apparently you can't `"AAA".into()`. I could have done a `from` on `Label`, but this is fine. 

Other than that, start with `AAA` and then iterate through the `simulation.moves` until you find `ZZZ`. The nice part here is `.iter().cycle()` which gives us an infinitely repeating iterator for more or less free!

And that's it. 12k steps or so and we're done. 

## Part 2

> Instead of starting at just `AAA`, start at all nodes `**A` (ending with an `A`). Simulate all agents in lockstep and end when *all* agents are at a node `**Z` (ends with `Z`). 

### Brute Force

Interesting. Well, let's try the brute force solution:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, ref simulation) = parse::simulation(&input).unwrap();
    assert_eq!(s.trim(), "");

    // Get all nodes that end in A
    let mut current = simulation
        .neighbors
        .keys()
        .filter(|l| l[2] == 'A')
        .cloned()
        .collect::<Vec<_>>();

    // Count cycles
    let mut result = 0;
    for m in simulation.moves.iter().cycle() {
        result += 1;
        if result % 100_000_000 == 0 {
            println!("{result}");
        }

        // Update all nodes
        current = current
            .into_iter()
            .map(|l| match m {
                Move::Left => simulation.neighbors[&l].left,
                Move::Right => simulation.neighbors[&l].right,
            })
            .collect::<Vec<_>>();

        // If all nodes end in Z, we can exit
        if current.iter().all(|l| l[2] == 'Z') {
            break;
        }
    }

    println!("{result}");
    Ok(())
}
```

The code isn't that bad. Instead of a single node, `current` is now a `Vec` of nodes (I could actually have used a slice, now that I think about it). 

About now, you're probably realizing that this might be an issue though (especially if you see that `result % 100_000_000` debug statement in the middle there)... just how *long* is it going to take for these all to get in sync? 

Well, I let the code run for a while... without actually getting an answer. So while I let that run, let's see if we can do any better.

### Detecting Cycles

So one thing to note: eventually all of the agents *have* to cycle. The input is repeating and there are only so many nodes in the graph, so eventually you are going to end up at the same node in the graph while on the same step of the input. At that point, you're guaranteed to hit exactly the same sequence of nodes again and again. 

So let's start there. 

```rust
// Get all nodes that end in A
let starts = simulation
    .neighbors
    .keys()
    .filter(|l| l[2] == 'A')
    .cloned()
    .collect::<Vec<_>>();

// For each node, determine how long of a cycle it has
// This will be where you see the same node + position in input list twice
let cycles = starts
    .iter()
    .map(|each| {
        let mut current = *each;
        let mut cycle_length: usize = 0;
        let mut count = 0;

        // Previous states: position in input list + node
        let mut visited = BTreeMap::new();

        for (i, m) in simulation.moves.iter().enumerate().cycle() {
            count += 1;

            // If we're in a final state we've seen before, we have a cycle
            if current[2] == 'Z' && visited.contains_key(&(i, current)) {
                let cycle_start: usize = visited[&(i, current)];
                cycle_length = count - cycle_start;
                break;
            }

            // Otherwise, record this state and update
            visited.insert((i, current), count);
            current = match m {
                Move::Left => simulation.neighbors[&current].left,
                Move::Right => simulation.neighbors[&current].right,
            };
        }

        cycle_length
    })
    .collect::<Vec<_>>();
```

To solve this, we're going to keep a `BTreeMap` of all position in input + node we've seen before and which tick we saw that on. This was a fun trick to find, that `.iter().enumerate().cycle()` will return `(position in cycle, move)` as opposed to `.iter().cycle().enumerate()` which would count on forever. 

Then, as mentioned, when we see an element in the `visited` map a second time, we've detected a cycle. The length is the current tick (`count`) minus when we last saw that state (the value in the `Map`). 

Originally, I thought that we'd need to return both the `cycle_start` and `cycle_length` here and then figure out some sort of solver over all `start + X * length`. 

I also considered 'what if there are multiple exit points in the cycle' (multiple nodes that end in `Z` that a single agent visits). But again, for this problem, that didn't end up mattering. 

But then I thought a bit mathy: what is the actual mathematical way of determining when two cycles overlap? [[wiki:least common multiple]]()!

So let's implement that real quick:

```rust
fn gcd(a: usize, b: usize) -> usize {
    if b == 0 {
        a
    } else {
        gcd(b, a % b)
    }
}

fn lcm(a: usize, b: usize) -> usize {
    a / gcd(a, b) * b
}
```

(That should be in `num::integer::lcm`, which would have required pulling in [`num`](https://crates.io/crates/num). It's interesting that's not in the standard library.)

And then apply the `lcm` to all of the `cycle_lengths`:

```rust
let result = cycles.clone().into_iter().reduce(lcm).unwrap();

println!("{result}");
Ok(())
```

I like `reduce`. It's like `fold` except takes the first entry as the base case and `reduces` each number into it. So it turns `lcm(a, b)` into a function that can take `lcm(*ls)`. 

In any case... it turns out that's *actually the right answer for the problem*.

I'm... still not actually sure why that worked without considering the offsets of where each cycle starts. The write up on [this StackExchange post](https://math.stackexchange.com/questions/2218763/how-to-find-lcm-of-two-numbers-when-one-starts-with-an-offset) did give me the hint that it wouldn't matter, but it still feels really weird to me. 

The idea that I didn't have to check multiple possible `Z` nodes for each cycle though, that's a matter of input. There's only a single `Z` for each agent--verified that while solving the problem. 

But... it worked? And I mostly understand why. So we'll go with it. 

## Performance

So, let's talk performance. How well do our solutions run?

```rust
$ just time 8 1

hyperfine --warmup 3 'just run 8 1'
Benchmark 1: just run 8 1
  Time (mean ± σ):      82.0 ms ±   4.2 ms    [User: 31.0 ms, System: 11.6 ms]
  Range (min … max):    77.8 ms …  90.5 ms    33 runs

$ just time 8 2

hyperfine --warmup 3 'just run 8 2'
Benchmark 1: just run 8 2
  Time (mean ± σ):     117.7 ms ±   7.1 ms    [User: 55.8 ms, System: 12.4 ms]
  Range (min … max):   106.3 ms … 130.8 ms    23 runs
```

Nice! Just about as fast as anything else. 

But... what about that elephant in the room. The brute force solution. It was still happily chugging away (I tried a few other answers there as well, including [`rayon`](https://crates.io/crates/rayon) and some code optimizations), but none of them finished. 

So... how long would it take to run? 

Well:

```bash 
$ time just run 8 2-brute | ts

cat data/$(printf "%02d" 8).txt | cargo run --release -p day$(printf "%02d" 8) --bin part2-brute
[2023-12-08 01:40:42] --- <ts> ---
   Compiling day08 v0.1.0 (/Users/jp/Projects/advent-of-code/2023-ws/solutions/day08)
    Finished release [optimized] target(s) in 0.16s
     Running `target/release/part2-brute`
[2023-12-08 01:41:08] 100000000
[2023-12-08 01:41:34] 200000000
[2023-12-08 01:42:00] 300000000
...
```

[[ts: Timestamping stdout|`ts`]]() is a script I wrote a long time ago that timestamps each line of `stdout`, so in this case we can get how long the program is running without having to actually do timing in our Rust code. 

As you can see, it's running at (very roughly) 20 seconds per *100 million* iterations. That's pretty fast. But... what's the actual answer? Roughly 9 *trillion*?

Oy. That's a very big number. 

So big in fact that the estimated time to get to that value is 2.5e6 seconds. That's... 27 *days* and change. 

Yeah, I didn't let that keep running. 

I am curious if anyone has a better explanation for why the `lcm` of just the `cycle_lengths` works, but for now, it does! Onward!