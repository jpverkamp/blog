---
title: "AoC 2023 Day 11: Big Banginator"
date: 2023-12-11 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 11: Cosmic Expansion](https://adventofcode.com/2023/day/11)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day11) for today (spoilers!)

{{<toc>}}

## Part 1

> Read a grid of `#` (stars) and `.` (empty space). For each completely empty line or row, add another. Calculate the sum of the [[wiki:Manhattan distances]]() between all pairs of stars. 

<!--more-->

### Parsing

Pretty much the same parsing as [[AoC 2023 Day 10: Pipinator|day 10]](), albeit even simpler. I'm going to go ahead and jump to `i128`, since I can almost guarantee that part 2 is going to be 'but bigger!'. 

```rust
#[derive(Debug, Clone, Copy, Eq, PartialEq, Ord, PartialOrd)]
pub struct Point {
    pub x: i128,
    pub y: i128,
}

impl Point {
    pub fn manhattan_distance(&self, other: &Point) -> i128 {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }
}

#[derive(Debug)]
pub struct Galaxy {
    pub stars: Vec<Point>,
}
```

Expansion is a little more interesting though (could be how I wrote it):

```rust
impl Galaxy {
    pub fn expand(&mut self) {
        let get_err = |f: fn(&Point) -> i128| {
            self.stars
                .iter()
                .map(f)
                .collect::<HashSet<_>>()
                .iter()
                .sorted()
                .fold((None, 0, BTreeMap::new()), |(last, err, mut errs), &v| {
                    let err = match last {
                        Some(last) => err + v - last - 1,
                        None => 0,
                    };
                    errs.insert(v, err);
                    (Some(v), err, errs)
                })
                .2
        };

        let x_err = get_err(|p| p.x);
        let y_err = get_err(|p| p.y);

        self.stars = self
            .stars
            .iter()
            .map(|p| Point {
                x: p.x + x_err[&p.x],
                y: p.y + y_err[&p.y],
            })
            .collect();
    }
}
```

First, I'm going to write up a helper closure `get_err` that will iterate across the unique `x` values, accumulating how many empty columns/rows there are between each set (with that `fold`). 

If any two values are off by exactly 1, there are no empty columns/rows between them, so `v - last - 1` will be 0 and `err` will remain the same. Because we're accumulating `err`, the first values will move a little, but each later value will move for it's own new row + each new row before. 

Then we do the same for `x_err` and `y_err`; then we can apply that to each point (every original `x`/`y` value is in `(x|y)_err`, so the lookup will always work). 

And that's really it:

```rust

fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let mut galaxy = Galaxy::from(input);

    galaxy.expand();

    let result = galaxy
        .stars
        .iter()
        .cartesian_product(galaxy.stars.iter())
        .map(|(a, b)| a.manhattan_distance(b))
        .sum::<i128>()
        / 2; // we're double counting

    println!("{result}");
    Ok(())
}
```

Other than dividing by 2 I suppose. 

## Part 2

> Expand each empty row 1 million times. 

Called it. :smile:

It's actually just a small tweak to `expand` to multiply by an `age` value:

```rust
// ...
.fold((None, 0, BTreeMap::new()), |(last, err, mut errs), &v| {
    let err = match last {
        Some(last) => err + (age - 1) * (v - last - 1),
        None => 0,
    };
    // ...
```

The solution itself just changes to:

```rust
// ...
galaxy.expand_n(1_000_000);
// ...
```

And that's it. 

I could certainly have used `expand_n` for part 1, but the big gotcha there is that age *is not* 1. Because we're replacing 1 row with 2, you actually want `expand_n(2)` to get the same answer. 

## Performance

```bash
$ just time 11 1

hyperfine --warmup 3 'just run 11 1'
Benchmark 1: just run 11 1
  Time (mean ± σ):     166.5 ms ±  66.0 ms    [User: 37.1 ms, System: 16.2 ms]
  Range (min … max):    99.3 ms … 326.4 ms    26 runs

$ just time 11 2

hyperfine --warmup 3 'just run 11 2'
Benchmark 1: just run 11 2
  Time (mean ± σ):     124.8 ms ±  30.2 ms    [User: 33.5 ms, System: 14.0 ms]
  Range (min … max):    99.9 ms … 195.3 ms    26 runs
```

It's interesting that part 2 runs faster, but I expect that's as much an artifact of benchmarking at this scale than anything. 

And it's well under a second, so all is well. 

I can only imagine what the runtime for that would look like if (for some reason) you tried to actually store the full galaxy and had to allocate memory for all that space! 