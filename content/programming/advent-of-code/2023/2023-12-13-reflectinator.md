---
title: "AoC 2023 Day 13: Reflectinator"
date: 2023-12-13 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 13: Point of Incidence](https://adventofcode.com/2023/day/13)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day13) for today (spoilers!)

{{<toc>}}

## Part 1

> You are given a grid of `.` and `#`. Find the (single) axis of reflection (between two rows or columns). 

<!--more-->

### Basic types and parsing

Expected sorts of data:

```rust
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub struct Point {
    pub x: isize,
    pub y: isize,
}

#[derive(Debug, Copy, Clone, Eq, PartialEq, Default)]
pub struct Bounds {
    pub min_x: isize,
    pub max_x: isize,
    pub min_y: isize,
    pub max_y: isize,
}

#[derive(Debug)]
pub struct AshFlow {
    pub bounds: Bounds,
    pub rocks: FxHashSet<Point>,
}
```

I've found that giving up half of the possible values of a `usize` in order to not have to think about underflow on subtraction. Such is life. 

Next, parse it:

```rust
impl From<&str> for AshFlow {
    fn from(input: &str) -> Self {
        let mut rocks = FxHashSet::default();
        let mut bounds = Bounds::default();

        for (y, line) in input.lines().enumerate() {
            for (x, c) in line.chars().enumerate() {
                if c == '#' {
                    let x = x as isize;
                    let y = y as isize;

                    rocks.insert(Point { x, y });
                    bounds.include(Point { x, y });
                }
            }
        }

        AshFlow { bounds, rocks }
    }
}
```

Which requires a bit more on `Bounds`:

```rust
impl Bounds {
    pub fn contains(&self, point: &Point) -> bool {
        point.x >= self.min_x
            && point.x <= self.max_x
            && point.y >= self.min_y
            && point.y <= self.max_y
    }

    fn include(&mut self, p: Point) {
        self.min_x = self.min_x.min(p.x);
        self.max_x = self.max_x.max(p.x);
        self.min_y = self.min_y.min(p.y);
        self.max_y = self.max_y.max(p.y);
    }
}
```

It does always include `(0, 0)`, which is suboptimal in a general case. Instead we should probably require the first value or default to `None`. But it works well enough for this case. 

### Reflection

Okay, we're dealing a lot with reflection here and the definitions are a little weird (because we're reflecting 'between' rows/columns). So let's write that out and test it:

```rust
impl Point {
    pub fn reflect_x(&self, axis: isize) -> Point {
        Point {
            x: if axis >= self.x {
                axis + (axis - self.x) + 1
            } else {
                axis - (self.x - axis) + 1
            },
            y: self.y,
        }
    }

    pub fn reflect_y(&self, axis: isize) -> Point {
        Point {
            x: self.x,
            y: if axis >= self.y {
                axis + (axis - self.y) + 1
            } else {
                axis - (self.y - axis) + 1
            },
        }
    }
}

#[cfg(test)]
mod point_test {
    use super::*;

    #[test]
    fn test_reflect_x() {
        // .p......r.
        // ----><----
        // 0123456789
        let p = Point { x: 1, y: 5 };
        assert_eq!(p.reflect_x(4), Point { x: 8, y: 5 });

        let p = Point { x: 8, y: 5 };
        assert_eq!(p.reflect_x(4), Point { x: 1, y: 5 });

        // ....pr....
        // ----><----
        // 0123456789
        let p = Point { x: 4, y: 7 };
        assert_eq!(p.reflect_x(4), Point { x: 5, y: 7 });

        let p = Point { x: 5, y: 7 };
        assert_eq!(p.reflect_x(4), Point { x: 4, y: 7 });
    }

    #[test]
    fn test_reflect_y() {
        // .p......r.
        // ----><----
        // 0123456789
        let p = Point { x: 5, y: 1 };
        assert_eq!(p.reflect_y(4), Point { x: 5, y: 8 });

        let p = Point { x: 5, y: 8 };
        assert_eq!(p.reflect_y(4), Point { x: 5, y: 1 });

        // ....pr....
        // ----><----
        // 0123456789
        let p = Point { x: 7, y: 4 };
        assert_eq!(p.reflect_y(4), Point { x: 7, y: 5 });

        let p = Point { x: 7, y: 5 };
        assert_eq!(p.reflect_y(4), Point { x: 7, y: 4 });
    }
}
```

Getting this right (ascii art and all!) took a bit, but it was worth it. One less thing to debug when we're actually solving the problem. 

### Solution

Okay, we have `Points`, `Bounds`, and `AshFalls`. How do we actually use this to solve the problem?

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();

    let input = io::read_to_string(stdin.lock())?;
    let result = input
        .split("\n\n")
        .collect::<Vec<_>>()
        .iter()
        .map(|input| {
            let ashflow = AshFlow::from(*input);
            let mut result = 0;

            // TODO: Is it possible to have more than one mirror?
            // in the input cases, no

            for x_axis in ashflow.bounds.min_x..ashflow.bounds.max_x {
                if ashflow.rocks.iter().all(|p| {
                    let pr = p.reflect_x(x_axis);
                    !ashflow.bounds.contains(&pr) || ashflow.rocks.contains(&pr)
                }) {
                    result += x_axis + 1;
                }
            }

            for y_axis in ashflow.bounds.min_y..ashflow.bounds.max_y {
                if ashflow.rocks.iter().all(|p| {
                    let pr = p.reflect_y(y_axis);
                    !ashflow.bounds.contains(&pr) || ashflow.rocks.contains(&pr)
                }) {
                    result += 100 * (y_axis + 1);
                }
            }

            result
        })
        .sum::<isize>();

    println!("{result}");
    Ok(())
}
```

It's a little weird to split on `\n\n`, but we have multiple inputs in one file and this seemed the best way to deal with that. 

Beyond that, the core of the function is the `for x_axis` (and `y`) loops. Basically, we're going to try every x and then every y. For each value, take `all` points `p` and calculate their reflection `pr`. If it's out of bounds, that's valid, otherwise it has to also be a rock. 

Scoring is a bit weird (and we have to adjust for 0-based indexing), but that's it. We have part 1. 

## Part 2

> Each input has exactly one point (a `smudge`) where you can swap a `.` for a `#` (or vice versa) and have a new axis of reflection.
>
> Note: The previous axis of reflection may or may not still be valid. 

### Refactoring

Two quick changes that I'll want to make for this, first a method to toggle rocks on and off:

```rust
// Used to smudge either way
fn toggle(ashflow: &mut AshFlow, p: &Point) {
    if ashflow.rocks.contains(p) {
        ashflow.rocks.remove(p);
    } else {
        ashflow.rocks.insert(*p);
    }
}
```

And second, factor out the method for finding the first reflection of a type:

```rust
// Find the first reflection
// on_x if reflecting about the x axis, false otherwise
// if ignore is set, don't return this axis
fn reflect(ashflow: &AshFlow, on_x: bool, ignore: Option<isize>) -> Option<isize> {
    let axis_range = if on_x {
        ashflow.bounds.min_x..ashflow.bounds.max_x
    } else {
        ashflow.bounds.min_y..ashflow.bounds.max_y
    };

    for axis in axis_range {
        if ignore == Some(axis) {
            continue;
        }

        if ashflow.rocks.iter().all(|p| {
            let pr = if on_x {
                p.reflect_x(axis)
            } else {
                p.reflect_y(axis)
            };
            !ashflow.bounds.contains(&pr) || ashflow.rocks.contains(&pr)
        }) {
            return Some(axis);
        }
    }

    None
}
```

This handles both `for (x|y)_axis` loops before, but also handles one additional case: if there was already an axis and you want to `ignore` it, specify it here and it will not be returned (instead, if there's another, that one will be). 

### Solution

With all that in place, we should be good to solve:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();

    let input = io::read_to_string(stdin.lock())?;
    let result = input
        .split("\n\n")
        .collect::<Vec<_>>()
        .iter()
        .map(|input| {
            let mut ashflow = AshFlow::from(*input);
            let mut result = 0;

            // TODO: Is it possible to have more than one mirror?
            // in the input cases, no

            // Calculate the old axis of reflection (to ignore)
            let old_x = reflect(&ashflow, true, None);
            let old_y = reflect(&ashflow, false, None);

            'found: for x_smudge in ashflow.bounds.min_x..=ashflow.bounds.max_x {
                for y_smudge in ashflow.bounds.min_y..=ashflow.bounds.max_y {
                    let p_smudge = Point {
                        x: x_smudge,
                        y: y_smudge,
                    };
                    toggle(&mut ashflow, &p_smudge);

                    // If we got a new x (or later a y) ignoring the one we already saw
                    // This is our solution, score it and stop looking

                    if let Some(new_x) = reflect(&ashflow, true, old_x) {
                        result += new_x + 1;
                        break 'found;
                    }

                    if let Some(new_y) = reflect(&ashflow, false, old_y) {
                        result += 100 * (new_y + 1);
                        break 'found;
                    }

                    toggle(&mut ashflow, &p_smudge);
                }
            }

            result
        })
        .sum::<isize>();

    println!("{result}");
    Ok(())
}
```

I like this code a lot more than part 1! The refactoring makes things nice and elegant. 

## Performance

Sometimes brute force is fast enough:

```bash
$ just time 13 1

hyperfine --warmup 3 'just run 13 1'
Benchmark 1: just run 13 1
  Time (mean ± σ):      98.3 ms ±   6.9 ms    [User: 30.5 ms, System: 11.8 ms]
  Range (min … max):    84.9 ms … 121.7 ms    31 runs

$ just time 13 2

hyperfine --warmup 3 'just run 13 2'
Benchmark 1: just run 13 2
  Time (mean ± σ):     101.7 ms ±   8.7 ms    [User: 33.5 ms, System: 12.0 ms]
  Range (min … max):    87.3 ms … 128.5 ms    30 runs
```