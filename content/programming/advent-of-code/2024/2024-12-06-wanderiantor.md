---
title: "AoC 2024 Day 6: Wanderinator"
date: 2024-12-06 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 6: Guard Gallivant](https://adventofcode.com/2024/day/6)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day6.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are given a grid of walls (`#`), floors (`.`), and a guard (`^`, initially facing up/north). The guard walks forward until they run into a wall at which point they turn right. How many tiles does the guard reach before leaving the map. 

<!--more-->

This is a great opportunity to use that `Grid` we introduced [last time]({{<ref "">}})!

```rust
#[derive(Debug, Copy, Clone, Default)]
enum Tile {
    #[default]
    Empty,
    Wall,
}

#[derive(Debug, Clone)]
struct Map {
    guard: Point,
    facing: Direction,
    grid: Grid<Tile>,
}

#[aoc_generator(day6)]
fn parse(input: &str) -> Map {
    let grid = Grid::read(input, &|c| match c {
        '.' => Tile::Empty,
        '#' => Tile::Wall,
        '^' => Tile::Empty,
        _ => panic!("Invalid character: {}", c),
    });

    let guard_index = input.find('^').unwrap();

    let per_row = grid.width + 1;
    let guard = Point::new(
        (guard_index % per_row) as i32,
        (guard_index / per_row) as i32,
    );
    let facing = Direction::Up;

    Map {
        guard,
        facing,
        grid,
    }
}
```

We do introduce two new structure (that I have used in previous years: `Point` and `Direction`). I've done a few new things, so let's see how those work.


### `Direction`

A `Direction` is something we need for the facing of the guard. It can be represented as North/South/East/West or Up/Down/Left/Right. For the moment, we'll go with the latter. It's mostly just a data structure. Here's the [full code](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/direction.rs).

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub enum Direction {
    Up,
    Down,
    Left,
    Right,
}

#[allow(dead_code)]
impl Direction {
    pub fn rotate_cw(&self) -> Direction {
        match self {
            Direction::Up => Direction::Right,
            Direction::Right => Direction::Down,
            Direction::Down => Direction::Left,
            Direction::Left => Direction::Up,
        }
    }

    pub fn rotate_right(&self) -> Direction {
        self.rotate_cw()
    }

    pub fn rotate_ccw(&self) -> Direction {
        match self {
            Direction::Up => Direction::Left,
            Direction::Left => Direction::Down,
            Direction::Down => Direction::Right,
            Direction::Right => Direction::Up,
        }
    }

    pub fn rotate_left(&self) -> Direction {
        self.rotate_ccw()
    }
}
```

### `Point`

Currently only a 32-bit number. I may decide to change that down the line when (I doubt this is an if) I need bigger numbers :smile:. It's signed because we quite often need to add/subtract negative points. 

The full code is [here](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/point.rs) if you're curious. Some specific bits:

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct Point {
    pub x: i32,
    pub y: i32,
}

#[allow(dead_code)]
impl Point {
    pub fn new(x: i32, y: i32) -> Self {
        Self { x, y }
    }

    pub fn manhattan_distance(&self, other: &Self) -> i32 {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }

    pub fn neighbors(&self) -> [Self; 4] {
        [
            *self + Direction::Up,
            *self + Direction::Down,
            *self + Direction::Left,
            *self + Direction::Right,
        ]
    }
}
```

Next up, I have standard implementations of `Add`, `AddAssign`, etc. But what's interesting is a few `From` conversions that I haven't done before:

```rust
impl From<(i32, i32)> for Point {
    fn from((x, y): (i32, i32)) -> Point {
        Point::new(x, y)
    }
}

impl From<(isize, isize)> for Point {
    fn from((x, y): (isize, isize)) -> Point {
        Point::new(x as i32, y as i32)
    }
}

impl From<(usize, usize)> for Point {
    fn from((x, y): (usize, usize)) -> Point {
        Point::new(x as i32, y as i32)
    }
}
```

This lets me take `isize` or `usize` tuples and turn them into `Point`, which is kind of neat. Of course, if those values are out of range, things will explode... but we'll just deal with that for the time being!

Otherwise, we also want the ability to turn a `Direction` into a `Point` (for adding) or adding them together:

```rust
// Interop between points and directions

impl From<Direction> for Point {
    fn from(direction: Direction) -> Point {
        match direction {
            Direction::Up => Point::new(0, -1),
            Direction::Down => Point::new(0, 1),
            Direction::Left => Point::new(-1, 0),
            Direction::Right => Point::new(1, 0),
        }
    }
}

impl std::ops::Add<Direction> for Point {
    type Output = Point;

    fn add(self, rhs: Direction) -> Self::Output {
        self + std::convert::Into::<Point>::into(rhs)
    }
}
```

### Actually solving the problem

Okay, we have the framework out of the way. 

To solve it, I'm going to implement a `Map::walk` function:

```rust
impl Map {
    fn walk(&self) -> Grid<bool> {
        let Map {
            mut guard,
            mut facing,
            grid,
        } = self;

        let mut visited = Grid::new(grid.width, grid.height);
        visited.set(guard, true);

        let mut duplicates = hashbrown::HashSet::new();
        duplicates.insert((guard, facing));

        while grid.in_bounds(guard) {
            match grid.get(guard + facing) {
                Some(Tile::Empty) => {
                    guard += facing.into();
                    visited.set(guard, true);
                }
                Some(Tile::Wall) => {
                    facing = facing.rotate_cw();
                }
                None => break,
            }
        }

        visited
    }
}
```

Essentially, this implements the algorithm described in the problem statement and returns a `Grid<bool>` of all the points the guard visits. We'll have a problem if the guard ever starts walking in a loop... but that's a problem for [part 2](#part-2). :smile:

Now that we have that, the actual solution is... count them!

```rust
#[aoc(day6, part1, v1)]
fn part1_v1(input: &Map) -> usize {
    input.walk(false).unwrap().iter().filter(|&v| *v).count()
}
```

That's it. :smile:

I suppose that needs an `iter` function on `Grid` (and I implemented an `iter_enumerate` for good measure that will also return the point for each):

```rust
impl Grid {
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.data.iter()
    }

    pub fn iter_enumerate(&self) -> impl Iterator<Item = (Point, &T)> {
        self.data
            .iter()
            .enumerate()
            .map(|(i, v)| ((i % self.width, i / self.width).into(), v))
    }
}
```

Running it:

```bash
$ cargo aoc --day 6 --part 1

AOC 2024
Day 6 - Part 1 - v1 : 5551
	generator: 59.375µs,
	runner: 38.458µs
```

Quick enough for now!

## Part 2

> How many points are there such that you can add exactly 1 wall to make the guard walk in a repeating loop? 

Told you we'd need to loop!

This does require a small modification to the `walk` function:

```rust
impl Map {
    fn walk(&self, check_loops: bool) -> Option<Grid<bool>> {
        let Map {
            mut guard,
            mut facing,
            grid,
        } = self;

        let mut visited = Grid::new(grid.width, grid.height);
        visited.set(guard, true);

        let mut duplicates = hashbrown::HashSet::new();
        duplicates.insert((guard, facing));

        while grid.in_bounds(guard) {
            match grid.get(guard + facing) {
                Some(Tile::Empty) => {
                    guard += facing.into();
                    visited.set(guard, true);
                }
                Some(Tile::Wall) => {
                    facing = facing.rotate_cw();
                }
                None => break,
            }

            if check_loops {
                if duplicates.contains(&(guard, facing)) {
                    return None;
                }
                duplicates.insert((guard, facing));
            }
        }

        Some(visited)
    }
}
```

I did leave it optional, since `Hash` isn't free. So if we don't think we need it, just don't use it. Part 1 with `check_loops=true`:

```bash
# With check_loops=false
$ cargo aoc --day 6 --part 1

AOC 2024
Day 6 - Part 1 - v1 : 5551
	generator: 59.375µs,
	runner: 38.458µs

# With check_loops=true
$ cargo aoc --day 6

AOC 2024
Day 6 - Part 1 - v1 : 5551
	generator: 56.875µs,
	runner: 159.667µs
```

Significant for such a small change. 

For the first round on this problem, let's brute force it. Try every single point on the grid (even if it's already a wall!). Run `walk` and check if we get `None`:

```rust
// For each point on the grid, check if adding a wall there would create a loop
#[aoc(day6, part2, v1)]
fn part2_v1(input: &Map) -> usize {
    iproduct!(0..input.grid.width, 0..input.grid.height)
        .filter(|&(x, y)| {
            // The 'visited' function returns None on loops (no path found)
            let mut input = input.clone();
            input.grid.set((x, y), Tile::Wall);
            input.walk(true).is_none()
        })
        .count()
}
```

`iproduct!` is a macro from [`itertools`](https://docs.rs/itertools/latest/itertools/) that basically will generate each point for me in a clean way. 

Anyways, how does it do?

```bash
$ cargo aoc --day 6 --part 2

AOC 2024
Day 6 - Part 2 - v1 : 1939
	generator: 50.583µs,
	runner: 1.584841459s
```

More than a second?! That cannot stand!

[First optimization](#optimization-1-only-checking-the-path)? We don't need to check *every* point.

After that, we're also doing a `clone` every iteration of the loop, which I suppose we can avoid by undoing each change. I'll have to [try that](#optimization-3-avoiding-clone). 

It is nice to have an answer to verify against though. 

### Optimization 1: Only checking the path

Okay, first optimization. Because the guard only changes their facing (and thus may introduce a loop) when they run into a wall, we can optimize by only putting walls where they might have some impact:

```rust
// Only check adding walls to the original path
// We don't have to check adjacent since you have to 'run into' a wall to turn
#[aoc(day6, part2, limited)]
fn part2_limited(input: &Map) -> usize {
    let visited = input.walk(false).unwrap();
    iproduct!(0..input.grid.width, 0..input.grid.height)
        .filter(|&(x, y)| {
            let p = Point::from((x, y));
            if visited.get(p) == Some(&true) {
                let mut input = input.clone();
                input.grid.set(p, Tile::Wall);
                input.walk(true).is_none()
            } else {
                false
            }
        })
        .count()
}
```

For this, we're going to run the algorithm one extra time first (basically part 1), to get all the points on the path. Then, we filter out any points that are not on the path and only check the rest. 

As mentioned in the comment, we don't have to check points adjacent to the path (I originally) did, since if you are 'beside' the original path, it won't turn. 

This is a bit more than 3x faster:

```bash
$ cargo aoc --day 6 --part 2

AOC 2024
Day 6 - Part 2 - v1 : 1939
	generator: 50.583µs,
	runner: 1.584841459s

Day 6 - Part 2 - limited : 1939
	generator: 54.084µs,
	runner: 377.670083ms
```

Not too bad, but we can do better!

### Optimization 2: Rayon parallelization

This problem fits pretty well into the [[wiki:embarrassingly parallel]]() category. Since we're cloning, we can check every single point at the same time (if we have enough CPU cores) and just add them up. Enter [`rayon`](https://docs.rs/rayon/latest/rayon/): easy to use (mostly) drop in parallelization!

```rust
// Add rayon parallelization
#[aoc(day6, part2, limited_rayon)]
fn part2_limited_rayon(input: &Map) -> usize {
    let visited = input.walk(false).unwrap();
    iproduct!(0..input.grid.width, 0..input.grid.height)
        .par_bridge()
        .into_par_iter()
        .map(|(x, y)| {
            let p = Point::from((x, y));

            if visited.get(p) == Some(&true) {
                let mut input = input.clone();
                input.grid.set(p, Tile::Wall);
                if input.walk(true).is_none() {
                    1
                } else {
                    0
                }
            } else {
                0
            }
        })
        .sum::<usize>()
}
```

Okay, it's not *quite* a free change. Because there's a bit of a change in API from a standard `Iter` to the `Itertools` `iproduct!`, we need to add a `par_bridge` to convert. After that, you appearnly can't `filter` in `rayon`, so instead we'll `map` and `sum`. But the general idea is the same!

```bash
$ cargo aoc --day 6 --part 2

AOC 2024
Day 6 - Part 2 - limited : 1939
	generator: 54.084µs,
	runner: 377.670083ms

Day 6 - Part 2 - limited_rayon : 1939
	generator: 50.667µs,
	runner: 44.247666ms
```

Another 10x speedup! Which is mostly due to the machine I'm running on. On a single core machine, it would probably run if anything a bit slower. But I like it, so in it stays!

### Optimization 3: Avoiding clone

One last thing to look at: `clone`. In both of the above cases, we `clone` the `input` on every iterations. We can't actually fix that in the parallel `rayon` case (because we don't want to mutate data in one thread that another might be trying to use), but we can for the single threaded case.

The basic idea: before running the inner `walk`, set the `Wall`. Then when we're done, unset it!

That's really it:

```rust
// Try without cloning the input (more than once)
#[aoc(day6, part2, no_clone)]
fn part2_limited_no_clone(input: &Map) -> usize {
    let mut input = input.clone();

    let visited = input.walk(false).unwrap();
    iproduct!(0..input.grid.width, 0..input.grid.height)
        // Any points not on or adjacent to original path cannot introduce a loop
        .filter(|&(x, y)| {
            let p = Point::from((x, y));
            if visited.get(p) == Some(&true) {
                input.grid.set((x, y), Tile::Wall);
                let result = input.walk(true).is_none();
                input.grid.set((x, y), Tile::Empty);
                result
            } else {
                false
            }
        })
        .count()
}
```

Unfortunately:

```bash
$ cargo aoc --day 6 --part 2

AOC 2024
Day 6 - Part 2 - v1 : 1939
	generator: 50.583µs,
	runner: 1.584841459s

Day 6 - Part 2 - limited : 1939
	generator: 54.084µs,
	runner: 377.670083ms

Day 6 - Part 2 - limited_rayon : 1939
	generator: 50.667µs,
	runner: 44.247666ms

Day 6 - Part 2 - no_clone : 1939
	generator: 39.209µs,
	runner: 376.155625ms
```

It's actually pretty much exactly the same speed as the initial `limited` case. This one is dominated by the cost of the `Hash` in loop detection. Still, it was an interesting idea I suppose. 

### Optimization 4: No hash

Speaking of which... didn't we say that `Hash` is expensive? (Even with `hashbrown`. It's worse with the built in hash function, since it has to make additional security guarantees). 

Instead of a duplicates `HashSet`, let's create 4 `Grid<bool>`, one for each direction:

```rust
impl Map {
    fn walk(&self, check_loops: bool) -> Option<Grid<bool>> {
        let Map {
            mut guard,
            mut facing,
            grid,
        } = self;

        let mut visited = Grid::new(grid.width, grid.height);
        visited.set(guard, true);

        let mut duplicates_up = Grid::new(grid.width, grid.height);
        duplicates_up.set(guard, true);

        let mut duplicates_left = Grid::new(grid.width, grid.height);
        let mut duplicates_right = Grid::new(grid.width, grid.height);
        let mut duplicates_down = Grid::new(grid.width, grid.height);

        while grid.in_bounds(guard) {
            match grid.get(guard + facing) {
                Some(Tile::Empty) => {
                    guard += facing.into();
                    visited.set(guard, true);
                }
                Some(Tile::Wall) => {
                    facing = facing.rotate_cw();
                }
                None => break,
            }

            if check_loops {
                let duplicates = &mut match facing {
                    Direction::Up => &mut duplicates_up,
                    Direction::Left => &mut duplicates_left,
                    Direction::Right => &mut duplicates_right,
                    Direction::Down => &mut duplicates_down,
                };

                if duplicates.get(guard) == Some(&true) {
                    return None;
                }
                duplicates.set(guard, true);
            }
        }

        Some(visited)
    }
}
```

That... is slightly ugly. But was it worth it? 

```bash
# hashmap 
$ cargo aoc --day 6 --part 2

AOC 2024
Day 6 - Part 2 - v1 : 1939
	generator: 50.583µs,
	runner: 1.584841459s

Day 6 - Part 2 - limited_rayon : 1939
	generator: 50.667µs,
	runner: 44.247666ms

# Grid<bool>
$ cargo aoc --day 6 --part 2

Day 6 - Part 2 - v1 : 1939
	generator: 45.666µs,
	runner: 409.640417ms

Day 6 - Part 2 - limited_rayon : 1939
	generator: 52µs,
	runner: 13.176792ms
```

Huh... that's pretty good. Even the original solution is sub half a second now!

Worth it!

## Benchmarks

Overall benchmarks:

```bash
# hashmap
cargo aoc bench --day 6

Day6 - Part1/v1             time:   [18.340 µs 18.428 µs 18.521 µs]
Day6 - Part2/v1             time:   [1.6568 s 1.6652 s 1.6735 s]
Day6 - Part2/limited        time:   [392.86 ms 394.18 ms 395.57 ms]
Day6 - Part2/limited_rayon  time:   [45.311 ms 45.548 ms 45.807 ms]
Day6 - Part2/no_clone       time:   [413.63 ms 416.32 ms 419.08 ms]

# Grid<bool>
$ cargo aoc bench --day 6

Day6 - Part1/v1             time:   [19.739 µs 19.906 µs 20.106 µs]
Day6 - Part2/v1             time:   [428.06 ms 429.59 ms 431.26 ms]
Day6 - Part2/limited        time:   [95.354 ms 95.921 ms 96.571 ms]
Day6 - Part2/limited_rayon  time:   [12.414 ms 12.441 ms 12.467 ms]
Day6 - Part2/no_clone       time:   [97.974 ms 98.957 ms 100.32 ms]
```

