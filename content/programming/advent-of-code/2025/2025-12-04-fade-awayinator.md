---
title: "AoC 2025 Day 4: Fade Awayinator"
date: 2025-12-04 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics:
- Algorithms
- Grid Algorithms
- Cellular Automata
- Neighbor Search
- Flood Fill
- Simulation
- Iteration
- Performance
- Benchmarking
- Code Optimization
- Rendering
- Visualization
- Rust Performance
---
## Source: [Day 4: Printing Department](https://adventofcode.com/2025/day/4)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day4.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a grid of solid `@` and empty cells `.`, count how many solid cells have less than 4 neighbors. 

<!--more-->

Okay, let's get a `Grid` going. I've done something similar to this a few times, so [here](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/grid.rs) is the newest iteration. Basically, a `Grid<T>` can story any `Copy` type (just to make some operations easier). 

You can build it from an `&str` by providing a function `Fn(char) -> T` and it will handle bounds checking. I did add a couple of interesting functions I hadn't done before:

```rust
impl<T> Grid<T>
where
    T: Copy,
{
    pub fn iter(&self) -> impl Iterator<Item = (isize, isize, T)> {
        (0..self.width)
            .flat_map(move |x| (0..self.height).map(move |y| (x, y, self.get(x, y).unwrap())))
    }

        pub fn neighbors(&self, x: isize, y: isize) -> impl Iterator<Item = Option<T>> {
        [
            (-1_isize, -1_isize),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        .into_iter()
        .map(move |(xd, yd)| self.get(x + xd, y + yd))
    }
}
```

Really, that should be implementing `Iter` but I suppose this works well enough. It's an `.iter` that will iterate over the `(x, y, v: T)`, so you can do all sorts of things (like only count `@` squares). And then `neighbors` will iterate over the 8 neighbors. 

All of which means we can implement this problem as:

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let g = Grid::read(input, |c| c == '@');

    g.iter()
        .filter(|(x, y, r)| 
            *r 
            && g.neighbors(*x, *y).filter(|v| *v == Some(true)).count() < 4
        )
        .count()
        .to_string()
}
```

Use the `.iter()` function and count only `@` tiles that have `< 4` neighbors that are `@`. That's it!

```bash
$ just run 4 part1

part1: 1393

$ just bench 4 part1

part1: 105.073µs ± 4.234µs [min: 103.167µs, max: 120.083µs, median: 103.5µs]
```

## Part 2

> Repeat the process until no more changes can be made. Count how many total `@` are removed. 

For this one, I don't just want `.iter()` I also want `map`. 

```rust
impl<T> Grid<T>
where
    T: Copy,
{
    pub fn map(&self, f: impl Fn(isize, isize, T) -> T) -> Grid<T> {
        Grid {
            width: self.width,
            height: self.height,
            data: self.iter().map(|(x, y, v)| f(x, y, v)).collect::<Vec<_>>(),
        }
    }
}
```

You provide a function that can map over `(x, y, V: T)` and it will create a new `Grid` from that:

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let mut g = Grid::read(input, |c| c == '@');
    let initial_count = g.iter().filter(|(_, _, v)| *v).count();
    let mut previous_count = initial_count;

    loop {
        let new_g = g.map(|x, y, v| 
            v
            && g.neighbors(x, y).filter(
                |v| *v == Some(true)
            ).count() >= 4
        );

        let new_count = new_g.iter().filter(|(_, _, v)| *v).count();

        if previous_count == new_count {
            return (initial_count - new_count).to_string();
        }

        g = new_g;
        previous_count = new_count;
    }
}
```

Which works:

```bash
$ just run 4 part2

8643

$ just bench 4 part2

part2: 4.882715ms ± 86.998µs [min: 4.727625ms, max: 5.216583ms, median: 4.877ms]
```

I think we can do a bit better than that though...

## Part 2 - No Map

One problem with the `Map` is that we're allocating a new map on each iteration. Let's do it with mutation instead:

```rust
#[aoc::register]
fn part2_no_map(input: &str) -> impl Into<String> {
    let mut g = Grid::read(input, |c| c == '@');
    let mut count = 0;

    loop {
        let mut changed = false;

        for x in 0..g.width() {
            for y in 0..g.height() {
                if g.get(x, y) == Some(true)
                    && g.neighbors(x, y).filter(|v| *v == Some(true)).count() < 4
                {
                    g.set(x, y, false);
                    changed = true;
                    count += 1;
                }
            }
        }

        if !changed {
            break;
        }
    }

    count.to_string()
}
```

Which is ~5x faster.

```bash
$ just run 4 part2_no_map

8643

$ just bench 4 part2_no_map

part2_no_map: 1.157833ms ± 25.989µs [min: 1.117667ms, max: 1.253459ms, median: 1.157167ms]
```

## Rendering

Another thing I like to do with these problems is to render the solutions. Sometimes they look *pretty cool*. So let's add that to my basic macro for this year:

* [render.rs](https://github.com/jpverkamp/advent-of-code/blob/master/2025/aoc_macros/src/render.rs)
* [lib.rs CLI](https://github.com/jpverkamp/advent-of-code/blob/master/2025/aoc_macros/src/lib.rs#L237)
* [lib.rs register_render](https://github.com/jpverkamp/advent-of-code/blob/master/2025/aoc_macros/src/lib.rs#L511)

This gives us a few new macros:

### `register_render`

```rust
#[aoc::register_render(scale = 4, fps = 10)]
fn part2_render(input: &str) {
    //...
}
```

This will register a function to the CLI for rendering, so you can `./day4 render part2_render`.

This doesn't actually render anything by itself.

The `scale` and `fps` are both optional. 

### `render_image!(width, height, filename, f)`

`width` and `height` are the size of the image to render, `filename` is... the filename, and `f` should be a function `Fn(usize, usize) -> (u8, u8, u8)` that maps each pixel to a color. 

### `render_frame!(width, height, f)`

The same parameters, but this one is a bit more interesting in implementation. What happens is that if any calls are made to `render_frame`, the macro will keep track of them. Then after the function is done, it will write all of those frames to disk and use `ffmpeg` to make a video. 

Pretty fun implementation. This one, I probably did half and half with an LLM. I'm not using them for the problems themselves, but this was something I've written before (albeit without the cool macro bits) and just want working. 

Granted, the implementation is... a bit weird? I might go back and rewrite it at some point. 

## Rendering Part 2

In any case, here's the rendering I made for this one!

```rust
#[aoc::register_render(scale = 4, fps = 10)]
fn part2_render(input: &str) {
    let mut g = Grid::read(input, |c| c == '@');

    loop {
        let mut removed = vec![];

        for x in 0..g.width() {
            for y in 0..g.height() {
                if g.get(x, y) == Some(true)
                    && g.neighbors(x, y).filter(|v| *v == Some(true)).count() < 4
                {
                    g.set(x, y, false);
                    removed.push((x, y));
                }
            }
        }

        aoc::render_frame!(g.width() as usize, g.height() as usize, |x, y| {
            if removed.contains(&(x as isize, y as isize)) {
                return (255, 0, 0);
            }

            match g.get(x as isize, y as isize) {
                Some(true) => (0, 0, 0),
                _ => (255, 255, 255),
            }
        });

        if removed.is_empty() {
            break;
        }
    }
}
```

Which makes this:

<video controls src="/embeds/2025/aoc/aoc2025_day4_part2_render.mp4"></video>

The black pixels are `@`, white are `.`, and red pixels are the ones just removed this iteration. 

Pretty cool!

## [Edit] Part 2 - Floodfill

Someone mentioned a bit of runtime analysis here. What if instead of going through the entire map until it stabilizes, we go through the entire map once, but at each point flood fill from there until we stop removing points? 

```rust
#[aoc::register]
fn part2_floodfill(input: &str) -> impl Into<String> {
    let mut g = Grid::read(input, |c| c == '@');
    let mut count = 0;

    for y in 0..g.height() {
        for x in 0..g.width() {
            // At each point, flood fill points we can remove 
            let mut stack = vec![(x, y)];
            while let Some((cx, cy)) = stack.pop() {
                // Any points we can't remove in the stack are ignored
                if g.get(cx, cy) != Some(true) {
                    continue;
                }
                if g.neighbors(cx, cy).filter(|v| *v == Some(true)).count() >= 4 {
                    continue;
                }

                // Remove point, add neighbors to stack
                g.set(cx, cy, false);
                count += 1;

                for nx in (cx - 1)..=(cx + 1) {
                    for ny in (cy - 1)..=(cy + 1) {
                        if nx == cx && ny == cy {
                            continue;
                        }
                        stack.push((nx, ny));
                    }
                }
            }
        }
    }

    count.to_string()
}
```

Which:

```bash
$ just run 4 part2_floodfill

8643

$ just bench 4 part2_floodfill

part2_floodfill: 666.912µs ± 26.553µs [min: 644.542µs, max: 824.167µs, median: 661.542µs]
```

Is actually ~2x as fast. Huh, neat. 

Rendered:

<video controls src="/embeds/2025/aoc/aoc2025_day4_part2_render_floodfill.mp4"></video>

(It looks a lot slower since I'm rendering one frame per pixel removed.)

## Benchmarks

```bash
$ just run 4

part1: 1393
part2: 8643
part2_no_map: 8643

$ just bench 4

part1: 107.041µs ± 5.007µs [min: 102.5µs, max: 121.5µs, median: 106.708µs]
part2: 4.826662ms ± 86.921µs [min: 4.70625ms, max: 5.170375ms, median: 4.807792ms]
part2_no_map: 1.164075ms ± 33.765µs [min: 1.115709ms, max: 1.286ms, median: 1.159042ms]
part2_floodfill: 670.268µs ± 19.006µs [min: 645.541µs, max: 752.125µs, median: 667.542µs]
```

| Day | Part | Solution          | Benchmark             |
| --- | ---- | ----------------- | --------------------- |
| 4   | 1    | `part1`           | 107.041µs ± 5.007µs   |
| 4   | 2    | `part2`           | 4.826662ms ± 86.921µs |
| 4   | 2    | `part2_no_map`    | 1.164075ms ± 33.765µs |
| 4   | 2    | `part2_floodfill` | 670.268µs ± 19.006µs  |