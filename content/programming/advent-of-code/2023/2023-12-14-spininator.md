---
title: "AoC 2023 Day 14: Spininator"
date: 2023-12-14 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 14: Parabolic Reflector Dish](https://adventofcode.com/2023/day/14)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day14) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a grid of `#` and `O` (among empty `.` points) where `O` can move, slide each `O` as far north as it can. Score each based on how far north it is. 

<!--more-->

Cellular automata! 

And an easier one too, it doesn't actually slide side to side, just in one direction. 

### Types and parsing

Okay, let's do it. Start with `Point` and `Bounds` from [[AoC 2023 Day 13: Reflectinator|yesterday]]() and add today's simulation:

```rust
#[derive(Debug, Clone)]
pub struct Platform {
    pub bounds: Bounds,
    pub round_rocks: Vec<Point>,
    pub cube_rocks: FxHashSet<Point>,
}

impl From<&str> for Platform {
    fn from(input: &str) -> Self {
        let mut bounds = Bounds::default();
        let mut round_rocks = Vec::default();
        let mut cube_rocks = FxHashSet::default();

        for (y, line) in input.lines().enumerate() {
            for (x, c) in line.chars().enumerate() {
                bounds.include(Point {
                    x: x as isize,
                    y: y as isize,
                });
                match c {
                    'O' => {
                        round_rocks.push(Point {
                            x: x as isize,
                            y: y as isize,
                        });
                    }
                    '#' => {
                        cube_rocks.insert(Point {
                            x: x as isize,
                            y: y as isize,
                        });
                    }
                    _ => {}
                }
            }
        }

        Self {
            bounds,
            round_rocks,
            cube_rocks,
        }
    }
}
```

### Simulation

So how does that translate to our problem?

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let mut platform = Platform::from(input.as_str());

    // Let the rocks slide until they stop moving
    loop {
        let mut changed = false;

        for i in 0..platform.round_rocks.len() {
            // Get current point; if we're at the top already, skip
            let r = platform.round_rocks[i];
            let next = Point { x: r.x, y: r.y - 1 };

            // Check that the next point is available
            if !platform.bounds.contains(&next)
                || platform.round_rocks.contains(&next)
                || platform.cube_rocks.contains(&next)
            {
                continue;
            }

            // If we get here, we can move; do it
            platform.round_rocks[i].y = next.y;
            changed = true;
        }

        if !changed {
            break;
        }
    }

    // Calculate final score
    let result = platform
        .round_rocks
        .iter()
        .map(|r| platform.bounds.max_y - r.y + 1)
        .sum::<isize>();

    println!("{result}");
    Ok(())
}
```

Not bad. 

It's not functional style, since if you `iter` over `platform.round_rocks`, things get a bit messy. 

One gotcha that I'm sure we're going to run into is the `platform.(round|cube)_rocks.contains`. Since we're storing it as a `Vec`, this is {{<inline-latex "O(n)">}}. But we'll get back to that. 

## Part 2

> Instead of just sliding north, slide first north, then east, then south, then west. Repeat this 1 *billion* times. 

Whelp. There it is. Performance is going to matter. 

### Solution: Spinning each way

To make this work, we'll define a few constants and `Add` and `Sub` on `Point`:

```rust
impl Point {
    pub const NORTH: Point = Point { x: 0, y: -1 };
    pub const SOUTH: Point = Point { x: 0, y: 1 };
    pub const EAST: Point = Point { x: 1, y: 0 };
    pub const WEST: Point = Point { x: -1, y: 0 };
}

impl std::ops::Add<Point> for Point {
    type Output = Point;

    fn add(self, rhs: Point) -> Self::Output {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
        }
    }
}

impl std::ops::Sub<Point> for Point {
    type Output = Point;

    fn sub(self, rhs: Point) -> Self::Output {
        Point {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
        }
    }
}
```

From there, we're going to fairly directly translate. For each cycle + each direction, slide in the right `direction` until we are stable:

```rust
for cycle in 0..=TARGET {
    // The rocks will slide N, W, S, E
    for direction in [Point::NORTH, Point::WEST, Point::SOUTH, Point::EAST] {
        // Let the rocks slide until they stop moving
        loop {
            let mut changed = false;

            for i in 0..platform.round_rocks.len() {
                let r = platform.round_rocks[i];
                let next = r + direction;

                // Check that the next point is available
                if !platform.bounds.contains(&next)
                    || platform.round_rocks.contains(&next)
                    || platform.cube_rocks.contains(&next)
                {
                    continue;
                }

                // If we get here, we can move; do it
                platform.round_rocks[i].x = next.x;
                platform.round_rocks[i].y = next.y;

                changed = true;
                break;
            }

            if !changed {
                break;
            }
        }
    }
}
```

I have no idea how slow this is... but let's go with *very*. I'm never going to wait a billion cycles for this. 

### Optimization 1: Cycle Detection

Luckily, as was the case in [[AoC 2023 Day 8: Mazinator|day 8]], we need to use some cycle detection.

```rust
let mut seen = FxHashMap::default();

for cycle in 0..=TARGET {
    // Check if we've seen this platform state before (it's deterministic, thus cycling)
    // Keep going until the cycle is in the same phase as the TARGET
    let key = platform.to_string();
    if let Some(cycle_start) = seen.get(&key) {
        let cycle_length = cycle - cycle_start;

        if (TARGET - cycle_start) % cycle_length == 0 {
            break;
        }
    }
    seen.insert(key, cycle);

    // ...
```

As mentioned, we're going to keep a map of the current `platform` to when we saw it before. If we see the same `platform` twice, we have a cycle. We don't need to immediately stop then, but rather stop once we're at the same point in that cycle that `TARGET` is. 

Hashing based on `platform.to_string` is a bit ugly, but it works well enough. More of the time is spent on updating than `to_string`, so no worries. 

Still pretty slow.

### Optimization 2: Data Structures

Okay, the next problem we're having is that `contains` on a `Vec` is a bit slow. So let's update our `Platform` struct a bit:

```rust
#[derive(Debug, Clone)]
pub struct PlatformV2 {
    pub bounds: Bounds,
    pub round_rocks: Vec<Point>,
    pub occupied: FxHashSet<Point>,
}

impl From<Platform> for PlatformV2 {
    fn from(value: Platform) -> Self {
        let mut occupied = FxHashSet::default();
        for r in value.round_rocks.iter() {
            occupied.insert(*r);
        }
        for c in value.cube_rocks.iter() {
            occupied.insert(*c);
        }

        Self {
            bounds: value.bounds,
            round_rocks: value.round_rocks,
            occupied,
        }
    }
}
```

Essentially, we're going to store some of the data (the `round_rocks`) twice in order to get some speedup. `occupied` will be used specifically for `contains`, since `HashSets` are fast for that, but we'll get the `Vec<Point>` for `round_rocks` so we can loop over it and modify it more easily:

```rust
// The rocks will slide N, W, S, E
for direction in [Point::NORTH, Point::WEST, Point::SOUTH, Point::EAST] {
    // Let the rocks slide until they stop moving
    loop {
        let mut changed = false;

        for i in 0..platform.round_rocks.len() {
            let r = platform.round_rocks[i];
            let next = r + direction;

            // Check that the next point is available
            if !platform.bounds.contains(&next) || platform.occupied.contains(&next) {
                continue;
            }

            // If we get here, we can move; do it
            platform.round_rocks[i].x = next.x;
            platform.round_rocks[i].y = next.y;

            platform.occupied.remove(&r);
            platform.occupied.insert(next);

            changed = true;
            break;
        }

        if !changed {
            break;
        }
    }
}
```

We do have to update both `round_rocks` and `occupied` (which could perhaps be hidden in an `impl` rather than trusting that I'll get it right), but it works. And for the first time, we actually have a solution!

```bash
$ just time 14 2-v2

hyperfine --warmup 3 'just run 14 2-v2'
Benchmark 1: just run 14 2-v2
  Time (mean ± σ):     18.358 s ±  0.172 s    [User: 17.818 s, System: 0.025 s]
  Range (min … max):   18.125 s … 18.627 s    10 runs
  ```

We can do better. 

### Optimization 3: Multislide

Okay, one thing we've been doing so far is sliding each rock one tile at a time--and sometimes not even that. If two rocks are touching and the 'second' tries to slide first, it will have to wait for the first to move. Something like this:

```text
# sliding right
.OO...
.O.O..
..O.O.
...O.O
....OO

# versus
.OO...
.O...O
....OO
```

But there's no particular reason we have to do it that way!

```rust
for i in 0..platform.round_rocks.len() {
    let r = platform.round_rocks[i];

    // Move in that direction until we hit something (or a wall)
    let mut next = r;
    loop {
        next = next + direction;

        if !platform.bounds.contains(&next) || platform.occupied.contains(&next) {
            // Have to step back to the last valid point
            next = next - direction;
            break;
        }
    }

    // If we didn't actually move, do nothing
    if next == r {
        continue;
    }

    // If we get here, we can move; do it
    platform.round_rocks[i].x = next.x;
    platform.round_rocks[i].y = next.y;

    platform.occupied.remove(&r);
    platform.occupied.insert(next);

    changed = true;
    break;
}
```

Does it help?

```bash
$ just time 14 2

hyperfine --warmup 3 'just run 14 2'
Benchmark 1: just run 14 2
  Time (mean ± σ):      6.110 s ±  0.215 s    [User: 5.781 s, System: 0.021 s]
  Range (min … max):    5.862 s …  6.340 s    10 runs
```

Absolutely. 

## Performance

Part 1 is fast...

```rust
$ just time 14 1

hyperfine --warmup 3 'just run 14 1'
Benchmark 1: just run 14 1
  Time (mean ± σ):     308.4 ms ± 162.7 ms    [User: 92.8 ms, System: 19.5 ms]
  Range (min … max):   165.0 ms … 525.7 ms    10 runs

$ just time 14 2

hyperfine --warmup 3 'just run 14 2'
Benchmark 1: just run 14 2
  Time (mean ± σ):      6.110 s ±  0.215 s    [User: 5.781 s, System: 0.021 s]
Range (min … max):    5.862 s …  6.340 s    10 runs
```

...but part 2 is unfortunately well over the 1 second mark, even with improvements. I really do think that I should be able to do better. But for now, this will have to do. We'll see!