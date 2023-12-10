---
title: "AoC 2023 Day 9: Stackinator"
date: 2023-12-09 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 9: Mirage Maintenance](https://adventofcode.com/2023/day/9)

## Part 1

> Given a list of terms, repeatedly calculate the differences of terms until these differences are 0. So:
>
>     0   3   6   9  12  15
>       3   3   3   3   3
>         0   0   0   0
>
> Calculate the sum of next terms for each sequence (18 for this one). 

<!--more-->

There's nothing particularly interesting about the types and parsing here:

```rust
#[derive(Debug)]
pub struct Equation {
    pub terms: Vec<i64>,
}

fn equation(s: &str) -> IResult<&str, Equation> {
    let (s, terms) = separated_list1(space1, complete::i64)(s)?;
    Ok((s, Equation { terms }))
}

pub fn equations(s: &str) -> IResult<&str, Vec<Equation>> {
    separated_list1(newline, equation)(s)
}
```

Honestly, I could have just kept `Vec` all through. 

What's a bit more interesting is a method to build the `stack` for an `Equation`:

```rust
impl Equation {
    // Generate a 'stack' of vecs, starting from the original terms
    // Each subsequent vec is the vec of differences in terms (and thus 1 element shorter)
    // Stop when that list is all 0s
    pub fn stack(&self) -> Vec<Vec<i64>> {
        let mut stack = vec![];
        stack.push(self.terms.clone());

        loop {
            let bottom = stack.last().unwrap();

            if bottom.iter().all(|t| *t == 0) {
                return stack;
            }

            stack.push(
                bottom
                    .iter()
                    .zip(bottom.iter().skip(1))
                    .map(|(a, b)| *b - *a)
                    .collect(),
            );
        }
    }
}
```

I enjoy the `zip(...)` of `iter()` and `iter().skip(1)`. 

With that, we just need to fill in the next numbers from 'bottom up':

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, equations) = parse::equations(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = equations
        .iter()
        .map(|equation| {
            // Build a stack of differences until we get to 0
            let mut stack = equation.stack();

            // From the bottom up, add the last value to the differences beneath it
            for i in (0..stack.len() - 1).rev() {
                let next = stack[i].last().unwrap() + stack[i + 1].last().unwrap();
                stack[i].push(next);
            }

            // The new last value of the top line (the original list)
            *stack[0].last().unwrap()
        })
        .sum::<i64>();

    println!("{result}");
    Ok(())
}
```

And there we have it. 

## Part 2

> Instead of summing the next terms for each equation, sum what would be the term before the current list. 

Almost, exactly the same code, we just have two differences:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, equations) = parse::equations(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = equations
        .iter()
        .map(|equation| {
            // Build the stacks as in part 1, but reverse them all (so we can generate a new 'first' element)
            // Alternatively, use a VecDeque
            let mut stack = equation.stack();
            stack.iter_mut().for_each(|v| v.reverse());

            // Same (from the bottom up), but this time we're subtracting
            for i in (0..stack.len() - 1).rev() {
                let next = stack[i].last().unwrap() - stack[i + 1].last().unwrap();
                stack[i].push(next);
            }

            // The new last value is the value 'before' the original list
            *stack[0].last().unwrap()
        })
        .sum::<i64>();

    println!("{result}");
    Ok(())
}
```

Specifically, we `for_each(|v| v.reverse())` and subtract instead of add. 

That's really all there is to it!

## Performance

Nothing much to say here:

```bash
$ just time 9 1

hyperfine --warmup 3 'just run 9 1'
Benchmark 1: just run 9 1
  Time (mean ± σ):      80.1 ms ±   3.3 ms    [User: 30.6 ms, System: 11.3 ms]
  Range (min … max):    77.2 ms …  89.4 ms    32 runs

$ just time 9 2

hyperfine --warmup 3 'just run 9 2'
Benchmark 1: just run 9 2
  Time (mean ± σ):      79.6 ms ±   3.9 ms    [User: 30.3 ms, System: 11.1 ms]
  Range (min … max):    77.2 ms …  95.5 ms    32 runs
```

Within a margin of error of each other, which is to be expected. The first `reverse` may have added some time, but it only depends on the length of input, not what the number of terms is. 

If we had *far* larger input, I might try to optimize this (I expect there are direct equations for these), but other than that... we're already sub 100ms and it's been a long day--so away we go!