---
title: "AoC 2025 Day 12: Knapsackinator"
date: 2025-12-12 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 12: Christmas Tree Farm](https://adventofcode.com/2025/day/12)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day12.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Solve the [[wiki:knapsack problem]]().
>
> ...
>
> ...
>
> But really, you are given a set of tiles (which all happen to be some subset of a 3x3) and a set of constraints--a MxN grid and how many of each tile to place. Count how many constraints are possible. 
>
> Tiles may be rotated and/or flipped.

<!--more-->

So, let's just do it. 

First, a tile:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Tile {
    id: usize,
    width: usize,
    height: usize,
    data: Vec<bool>,
}

impl From<&str> for Tile {
    fn from(value: &str) -> Self {
        let mut lines = value.lines();
        let id = lines
            .next()
            .unwrap()
            .strip_suffix(':')
            .unwrap()
            .parse::<usize>()
            .unwrap();

        let mut data = Vec::new();

        let mut height = 0;
        while let Some(line) = lines.next()
            && !line.trim().is_empty()
        {
            height += 1;

            for c in line.chars() {
                data.push(c == '#');
            }
        }
        let width = data.len() / height;

        Tile {
            id,
            width,
            height,
            data,
        }
    }
}
```

And some helper methods that can generate variations of the tile:

```rust
impl Tile {
    fn rotate_cw(&self) -> Self {
        let mut new_data = vec![false; self.data.len()];

        for y in 0..self.height {
            for x in 0..self.width {
                let old_index = x + y * self.width;
                let new_x = self.height - 1 - y;
                let new_y = x;
                let new_index = new_x + new_y * self.height;
                new_data[new_index] = self.data[old_index];
            }
        }

        Tile {
            id: self.id,
            width: self.height,
            height: self.width,
            data: new_data,
        }
    }

    fn flip_h(&self) -> Self {
        let mut new_data = vec![false; self.data.len()];

        for y in 0..self.height {
            for x in 0..self.width {
                let old_index = x + y * self.width;
                let new_x = self.width - 1 - x;
                let new_y = y;
                let new_index = new_x + new_y * self.width;
                new_data[new_index] = self.data[old_index];
            }
        }

        Tile {
            id: self.id,
            width: self.width,
            height: self.height,
            data: new_data,
        }
    }

    fn variations(&self) -> Vec<Tile> {
        let mut vars = Vec::new();
        let mut current = self.clone();
        vars.push(current.clone());

        for _ in 0..4 {
            let rotated = current.rotate_cw();
            if !vars.contains(&rotated) {
                vars.push(rotated.clone());
            }

            let flipped = current.flip_h();
            if !vars.contains(&flipped) {
                vars.push(flipped.clone());
            }

            current = current.rotate_cw();
        }

        vars
    }
}
```

Then, we'll write this up as a recursive solver, try to place each block and recur. If we find a solution, we're done. If we don't, backtrack. Eventually, if we try every combination, we know it's impossible. (Which is what makes this an [[wiki:NP-complete]]() problem). 

We can optimize a few things:

* Memoize (which because of the next line can be done between problems)
* If we have a complete edge row/column, we can solve a smaller problem without it
* If we have more area in tiles to place than we have area left, immediately return false

So building that up from the inside out, first we have a function to try to place a tile:

```rust
#[tracing::instrument(skip(grid, tile), fields(tile_id = tile.id, x, y), ret)]
fn try_place(grid: &mut Grid<Option<usize>>, tile: &Tile, x: isize, y: isize) -> bool {
    if log::log_enabled!(log::Level::Debug) {
        log::debug!(
            "Try place tile:\n{}  \non:\n{}",
            stringify_tile(tile),
            stringify_grid(grid)
        );
    }

    for ty in 0..tile.height as isize {
        for tx in 0..tile.width as isize {
            let gx = x + tx;
            let gy = y + ty;

            if gx < 0 || gy < 0 || gx >= grid.width() || gy >= grid.height() {
                return false;
            }

            if !tile.data[(tx as usize) + (ty as usize) * tile.width] {
                continue;
            }

            let grid_value = grid.get(gx, gy).unwrap();
            if grid_value.is_some() {
                return false;
            }
        }
    }

    for ty in 0..tile.height as isize {
        for tx in 0..tile.width as isize {
            let gx = x + tx;
            let gy = y + ty;

            if tile.data[(tx as usize) + (ty as usize) * tile.width] {
                grid.set(gx, gy, Some(tile.id));
            }
        }
    }

    true
}
```

And then one that will do the actual recursion:

```rust
#[tracing::instrument(skip(grid, tiles, memo, memo_stats, last_debug), ret)]
fn can_place(
    grid: &Grid<Option<usize>>,
    tiles: &Vec<Tile>,
    counts: &Vec<usize>,
    memo: Arc<Mutex<HashMap<(Grid<Option<usize>>, Vec<usize>), bool>>>,
    memo_stats: Arc<Mutex<(usize, usize)>>,
    last_debug: Arc<Mutex<Instant>>,
) -> bool {
    let cache_key = (grid.clone(), counts.clone());
    if log::log_enabled!(log::Level::Info) {
        if log::log_enabled!(log::Level::Debug)
            || last_debug.lock().unwrap().elapsed().as_secs() >= 5
        {
            log::info!(
                "Current progress [counts: {counts:?}, memo size: {}, hits: {}, misses: {}]:\n{}",
                memo.lock().unwrap().len(),
                memo_stats.lock().unwrap().0,
                memo_stats.lock().unwrap().1,
                stringify_grid(grid)
            );
            *last_debug.lock().unwrap() = Instant::now();
        }
    }

    if memo.lock().unwrap().contains_key(&cache_key) {
        memo_stats.lock().unwrap().0 += 1;
        return memo.lock().unwrap()[&cache_key];
    } else {
        memo_stats.lock().unwrap().1 += 1;
    }

    if counts.iter().all(|&c| c == 0) {
        memo.lock().unwrap().insert(cache_key, true);
        return true;
    }

    // If the sum of tiles we have left is not enough to fill the remaining empty cells, fail early
    let empty_cells = grid.iter().filter(|(_, _, v)| v.is_none()).count();
    let tiles_left = counts
        .iter()
        .zip(tiles.iter())
        .map(|(&c, t)| c * t.data.iter().filter(|&&b| b).count())
        .sum::<usize>();
    if tiles_left > empty_cells {
        memo.lock().unwrap().insert(cache_key, false);
        return false;
    }

    // If an entire edge row or column is full, we can remove it to reduce the problem size
    if (0..grid.width() as isize).all(|x| grid.get(x, 0).unwrap().is_some()) {
        let mut new_grid = grid.clone();
        new_grid.drop_row(0);
        return can_place(&new_grid, tiles, counts, memo, memo_stats, last_debug);
    }
    if (0..grid.width() as isize).all(|x| grid.get(x, grid.height() - 1).unwrap().is_some()) {
        let mut new_grid = grid.clone();
        new_grid.drop_row(grid.height() - 1);
        return can_place(&new_grid, tiles, counts, memo, memo_stats, last_debug);
    }
    if (0..grid.height() as isize).all(|y| grid.get(0, y).unwrap().is_some()) {
        let mut new_grid = grid.clone();
        new_grid.drop_column(0);
        return can_place(&new_grid, tiles, counts, memo, memo_stats, last_debug);
    }
    if (0..grid.height() as isize).all(|y| grid.get(grid.width() - 1, y).unwrap().is_some()) {
        let mut new_grid = grid.clone();
        new_grid.drop_column(grid.width() - 1);
        return can_place(&new_grid, tiles, counts, memo, memo_stats, last_debug);
    }

    // Always try to place the first tile we have available
    let tile_index = counts.iter().position(|&c| c > 0).unwrap();
    let tile = &tiles[tile_index];

    for y in 0..grid.height() as isize {
        for x in 0..grid.width() as isize {
            for variation in tile.variations() {
                let mut grid_clone = grid.clone();
                if try_place(&mut grid_clone, &variation, x, y) {
                    let mut new_counts = counts.clone();
                    new_counts[tile_index] -= 1;

                    if can_place(
                        &grid_clone,
                        tiles,
                        &new_counts,
                        memo.clone(),
                        memo_stats.clone(),
                        last_debug.clone(),
                    ) {
                        memo.lock().unwrap().insert(cache_key, true);
                        return true;
                    }
                }
            }
        }
    }

    memo.lock().unwrap().insert(cache_key, false);
    false
}
```

And then the main program (with Rayon for good measure):

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let mut tiles = Vec::new();

    let mut remaining_input = input;
    while let Some(next_end) = remaining_input.find("\n\n") {
        let tile_str = &remaining_input[..next_end];
        let tile = Tile::from(tile_str);
        tiles.push(tile);
        remaining_input = &remaining_input[next_end + 2..];
    }

    let memo = Arc::new(Mutex::new(HashMap::default()));
    let memo_stats = Arc::new(Mutex::new((0, 0)));

    remaining_input
        .lines()
        .enumerate()
        .par_bridge()
        .filter(|(line_index, line)| {
            let (size, rest) = line.split_once(": ").unwrap();
            let (width, height) = size.split_once('x').unwrap();
            let width: usize = width.parse().unwrap();
            let height: usize = height.parse().unwrap();

            let counts: Vec<usize> = rest.split(' ').map(|part| part.parse().unwrap()).collect();
            let initial_grid = Grid::new(width, height, None);
            let last_debug = Arc::new(Mutex::new(Instant::now()));

            can_place(
                &initial_grid,
                &tiles,
                &counts,
                memo.clone(),
                memo_stats.clone(),
                last_debug.clone(),
            )
        })
        .count()
        .to_string()
}
```

The `Arc<Mutux<...>>` allow sharing the cache between threads. There's some cost to locking it, but the ability to run a bunch of these at once outweighs that. 

And that's... it. It run quickly enough.

```bash
$ RUST_LOG=info just run 12 part1

[2025-12-13T18:14:41Z INFO  day12] part1 took 80.786759791s
575
```

Actually far more quickly than it should...

## Part 1 - It's actually trivial

So it turns out there is one more optimization that we were missing:

* If you have enough 3x3 empty spaces large enough to fit all of the tiles, there is a trivial solution (just give them each their own space)

```rust
#[aoc::register]
fn part1_trivial(input: &str) -> impl Into<String> {
    let mut tiles = Vec::new();

    let mut remaining_input = input;
    while let Some(next_end) = remaining_input.find("\n\n") {
        let tile_str = &remaining_input[..next_end];
        let tile = Tile::from(tile_str);
        tiles.push(tile);
        remaining_input = &remaining_input[next_end + 2..];
    }

    // This is the case for given input, this won't generalize to all possible sizes
    assert!(
        tiles.iter().all(|t| t.width == 3 && t.height == 3),
        "Only trivial 3x3 tiles supported"
    );

    let mut count = 0;

    for (line_index, line) in remaining_input.lines().enumerate() {
        let (size, rest) = line.split_once(": ").unwrap();
        let (width, height) = size.split_once('x').unwrap();
        let width: usize = width.parse().unwrap();
        let height: usize = height.parse().unwrap();

        log::info!("Line {line_index}: {width}x{height}");

        let counts: Vec<usize> = rest.split(' ').map(|part| part.parse().unwrap()).collect();

        // Trivially allowed: all tiles fit into their own 3x3 cell
        let tiles_allowed = (width / 3) * (height / 3);
        let total_tiles_requested: usize = counts.iter().sum();
        if total_tiles_requested <= tiles_allowed {
            count += 1;
            continue;
        }

        // Trivially impossible: not enough cells to hold the tiles no matter what
        let total_hashes_requested: usize = counts
            .iter()
            .zip(tiles.iter())
            .map(|(&c, t)| c * t.data.iter().filter(|&&b| b).count())
            .sum();
        let total_hashes_possible = width * height;
        if total_hashes_requested > total_hashes_possible {
            continue;
        }

        panic!("Required non-trivial check for line {line_index}");
    }

    count.to_string()
}
```

Which...

```bash
$ just run-and-bench 12 part1_trivial

575

part1_trivial: 159.753µs ± 7.564µs [min: 146.583µs, max: 183.125µs, median: 156.875µs]
```

Is honestly kind of disappointing for what will end up being the last AOC problem today? (Like previous years, the last day has only 1 part if you've completed everything else). 

So it goes. We do have pretty pictures yet to do!

## Rendering

Okay, let's render these. 

First, the example where there is a successful solution:

<video style="width: 400px; max-width: 100%;" controls src="/embeds/2025/aoc/aoc2025_day12_part1_example2.mp4" title="Title"></video>

And the one where there is not:

<video style="width: 400px; max-width: 100%;" controls src="/embeds/2025/aoc/aoc2025_day12_part1_example3.mp4" title="Title"></video>

That... is sped up by 1000x. The full video would be almost two *days* long. Granted, it solves it somewhat quicker than that, but still. That's a good example of just how bad this problem can get. 

So what does our actual input look like?

<video controls src="/embeds/2025/aoc/aoc2025_day12_part1.mp4" title="Title"></video>

That's just fun to watch. This isn't my whole input but rather any that have a valid solution in the first 32. Because of the 'not enough space' optimization, any invalid cases are just immediately eliminated. 

You can also play a bit with the algorithm to choose which tile is next. If you use the lowest index, you get the above. If you instead use whichever has the most left to place you get this:

<video controls src="/embeds/2025/aoc/aoc2025_day12_part1_by_most.mp4" title="Title"></video>

And if you choose randomly, you might get this:

<video controls src="/embeds/2025/aoc/aoc2025_day12_part1_random.mp4" title="Title"></video>

## Benchmarks

```bash
$ cargo run --release --bin day12 -- bench part1 --warmup 0 --iters 1 input/2025/day12.txt

part1: 96.430551417s ± 0ns [min: 96.430551417s, max: 96.430551417s, median: 96.430551417s]

$ just bench 12 part1_trivial

part1_trivial: 153.807µs ± 8.791µs [min: 145.916µs, max: 200.459µs, median: 150.917µs]
```

| Day | Part | Solution        | Benchmark           |
| --- | ---- | --------------- | ------------------- |
| 12  | 1    | `part1`         | 96.430551417s ± 0ns |
| 12  | 1    | `part1_trivial` | 153.807µs ± 8.791µs |