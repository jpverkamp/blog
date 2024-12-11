---
title: "AoC 2024 Day 4: Gridnator"
date: 2024-12-04 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Word Search
---
## Source: [Day 4: Ceres Search](https://adventofcode.com/2024/day/4)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day4.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a grid of letters, count how many times `XMAS` appears in any direction (horizontally, vertically, diagonally; forward or backward).

<!--more-->

### `Grid`

As we have in years past, time to bring out a `Grid`!

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Grid<T> {
    pub(crate) width: usize,
    pub(crate) height: usize,
    data: Vec<T>,
}

impl<T> Grid<T>
where
    T: Default + Clone + Sized,
{
    pub fn read(input: &str, f: &dyn Fn(char) -> T) -> Self {
        let mut width = 0;
        let mut height = 0;
        let mut data = Vec::new();

        for line in input.lines() {
            if line.is_empty() {
                continue;
            }

            width = line.len();
            height += 1;

            for c in line.chars() {
                data.push(f(c));
            }
        }

        Self {
            width,
            height,
            data,
        }
    }

    pub fn to_string(&self, f: &dyn Fn(&T) -> char) -> String {
        let mut s = String::new();

        for y in 0..self.height {
            for x in 0..self.width {
                s.push(f(&self.data[y * self.width + x]));
            }
            s.push('\n');
        }

        s
    }

    pub fn get(&self, x: usize, y: usize) -> Option<&T> {
        if x < self.width && y < self.height {
            Some(&self.data[y * self.width + x])
        } else {
            None
        }
    }

    pub fn iget(&self, x: isize, y: isize) -> Option<&T> {
        if x >= 0 && y >= 0 {
            self.get(x as usize, y as usize)
        } else {
            None
        }
    }
}
```

Basically, something that is designed to be read from a grid of characters into any type `T`. You have to given it a function to `read` each value (which is funny, because I'm just directly storing them for this problem) and/or `write` it back out if needed, but other than that, it handles parsing, sizing, and boundary checking well enough.

One difference this year is that I allow accessing by either `usize` or `isize`, the latter so that you can do things like `x - 1` safely enough (it will return `None` for out of bounds). 

One gotcha here is, if you're directly using the `char`, this is a bit inefficient, since it will just call an identity on each and every input character. I'm going to go with 'fast enough' and perhaps the compiler will realize and optimize that out for the `Grid<char>` case. 

So now, if wwant to `parse` the problem:

```rust
#[aoc_generator(day4)]
fn parse(input: &str) -> Grid<char> {
    fn id(c: char) -> char {
        c
    }

    Grid::read(input, &id)
}
```

Anyways, on to the problem!

### Iterating over `XMAS`

Okay, the general idea is that we'll check each `(x, y)` in the grid in each of the 8 possible directions. For each of those, check that the characters are `XMAS`, bailing early/as soon as possible for any mismatches. 


```rust
#[aoc(day4, part1, inner_looping)]
fn part1_original(grid: &Grid<char>) -> i32 {
    let mut count = 0;

    // For each starting point
    for x in 0..grid.width {
        for y in 0..grid.height {
            // Ignore any that don't start with X
            if grid.get(x, y) != Some(&'X') {
                continue;
            }

            // For each direction
            for dx in -1..=1 {
                'one_direction: for dy in -1..=1 {
                    // But have to be moving
                    if dx == 0 && dy == 0 {
                        continue;
                    }

                    // Iterate up to the remaining 3 characters in that direction
                    let mut xi = x as isize;
                    let mut yi = y as isize;

                    for target in ['M', 'A', 'S'].iter() {
                        xi += dx;
                        yi += dy;

                        if let Some(c) = grid.iget(xi, yi) {
                            if c != target {
                                continue 'one_direction;
                            }
                        } else {
                            continue 'one_direction;
                        }
                    }

                    count += 1;
                }
            }
        }
    }

    count
}
```

It does have one slight optimization, if you're not starting on `X`, don't even bother checking each direction. So I suppose that saves a handful of comparisons for any non-`X` squares. 

Other than that, check in that direction and `continue 'one_direction` as soon as a character doesn't match. 

Yes, I did name it that on purpose. :smile:

I do appreciate that Rust has named `break`/`continue`.

```bash
$ cargo aoc --day 4 --part 1

AOC 2024
Day 4 - Part 1 - inner_looping : 2406
	generator: 35.917µs,
	runner: 231.166µs
```

Performance wise, it falls well into the 'fast enough' category. Onward!

If you'd like to see the algorithm in action:

<video controls src="/embeds/2024/aoc/day4-part1-example.mp4" width="100%"></video>

Or on the entire image:

<video controls src="/embeds/2024/aoc/day4-part1.mp4" width="100%"></video>

(That's running at ~40x. The full render took... a while.)


### Optimization 1: Less loops

Okay, that's fine and mostly as quick as it could be, but I don't *really* like the extra inner loop (`target`). I feel like it's a bit weird to read and (maybe?) slower. Let's try to inline that:

```rust
#[aoc(day4, part1, direct)]
fn part1(grid: &Grid<char>) -> i32 {
    let mut count = 0;

    // For each starting point
    for x in 0..grid.width {
        for y in 0..grid.height {
            // Ignore any that don't start with X
            if grid.get(x, y) != Some(&'X') {
                continue;
            }

            // Local (shadowing) signed copies
            let x = x as isize;
            let y = y as isize;

            // For each direction
            for dx in -1..=1 {
                for dy in -1..=1 {
                    if dx == 0 && dy == 0 {
                        continue;
                    }

                    if grid.iget(x + dx, y + dy) == Some(&'M')
                        && grid.iget(x + 2 * dx, y + 2 * dy) == Some(&'A')
                        && grid.iget(x + 3 * dx, y + 3 * dy) == Some(&'S')
                    {
                        count += 1;
                    }
                }
            }
        }
    }

    count
}
```

We're still checking `X` once per `(x, y)`, but now we're directly checking each `(x + n * dx, y + n * dy)` inline (still shortcircuiting because of the `&&`). 

```bash
$ cargo aoc --day 4 --part 1

AOC 2024
Day 4 - Part 1 - inner_looping : 2406
	generator: 35.917µs,
	runner: 231.166µs

Day 4 - Part 1 - direct : 2406
	generator: 46.583µs,
	runner: 190.75µs
```

I'm not sure that level of performance would be worth it on it's own, but honestly I think the code is cleaner too, so win/win! 

## Part 2

> Instead of `XMAS`, find `MAS` in an X! Like this:
>   ```
>   M.S
>   .A.
>   M.S
>   ```
>
> Any direction is still allowed--the two Ms can be on the left, right, top or bottom.  

I'm glad I did the inline case above, since using a loop for this one would just be weird. 

```rust
#[aoc(day4, part2)]
fn part2(grid: &Grid<char>) -> i32 {
    let mut count = 0;

    // Each center point of the X
    for x in 1..(grid.width - 1) {
        for y in 1..(grid.height - 1) {
            // All grids have an A in the center
            if grid.get(x, y) != Some(&'A') {
                continue;
            }

            // Local (shadowing) signed copies
            let x = x as isize;
            let y = y as isize;

            // Each direction
            // This could be an || but I think this is easier to read :shrug:
            #[allow(clippy::if_same_then_else)]
            for delta in [-1, 1] {
                // Check the 4 corners horizontally
                if grid.iget(x + delta, y + 1) == Some(&'M')
                    && grid.iget(x + delta, y - 1) == Some(&'M')
                    && grid.iget(x - delta, y + 1) == Some(&'S')
                    && grid.iget(x - delta, y - 1) == Some(&'S')
                {
                    count += 1;
                }
                // And vertically
                else if grid.iget(x + 1, y + delta) == Some(&'M')
                    && grid.iget(x - 1, y + delta) == Some(&'M')
                    && grid.iget(x + 1, y - delta) == Some(&'S')
                    && grid.iget(x - 1, y - delta) == Some(&'S')
                {
                    count += 1;
                }
            }
        }
    }

    count
}
```

As before, check that the main point is correct (the central `A` in this case). If it is, we have 4 possible directions we could be going in:

* `M` on the left two, `S` on the right
* `M` on the right two, `S` on the left
* `M` on the top two, `S` on the bottom
* `M` on the bottom two, `S` on the top

Really, we have one ±1 and then check both in the other direction (which is a weird way to say it). Thus the `delta in [-1, 1]` above for the ±1 and the two checks for the 'other direction'. That covers all 4. 

```bash
$ cargo aoc --day 4 --part 2

Day 4 - Part 2 : 1807
	generator: 28.792µs,
	runner: 113.125µs
```

I do find it amusing that part 2 is faster... but it actually makes sense. We're checking half as many cases (4 instead of the 8 directions above) and only 4 characters per direction (`MMSS`) rather than the 3 `MAS` above. So you'd expect it to be roughly 2/3x... and without [benchmarking](#benchmarks), it's 159/240x = 0.6625x. :smile:

## Benchmarks

```bash
$ cargo aoc bench --day 4

Day4 - Part1/direct         time:   [123.63 µs 126.87 µs 130.22 µs]
Day4 - Part1/inner_looping  time:   [174.13 µs 175.77 µs 177.38 µs]
Day4 - Part2/(default)      time:   [71.537 µs 72.861 µs 74.209 µs]
```

Onward!