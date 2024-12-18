---
title: "AoC 2024 Day 18: Last Chancinator"
date: 2024-12-18 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics: []
---
## Source: [Day 18: RAM Run](https://adventofcode.com/2024/day/18)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day18.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are given a series of points on a `71x71` grid. Taking only the first 1024 points, how long is the shortest path from `(0, 0)` to `(70, 70)`?

<!--more-->

I'm going to skip the parsing, since it's not super interesting. I do add a special header for the example case (since it's 6x6 instead of 70x70), but that's about it. The code is [here](https://github.com/jpverkamp/advent-of-code/blob/b7d8ab1c691d0f07d0b81cd583cbc31fd6d29b57/2024/src/day18.rs#L56-L85) if you're interested.

This is just [[wiki:A-star search|A*]]() again.

```rust
#[aoc(day18, part1, v1)]
fn part1_v1(input: &Puzzle) -> i32 {
    let end = (input.width - 1, input.height - 1).into();

    match pathfinding::prelude::astar(
        &Point::ZERO,
        |&point| {
            Direction::all()
                .iter()
                .filter_map(|d| {
                    let new_p = point + *d;
                    if new_p.x < 0
                        || new_p.y < 0
                        || new_p.x >= input.width as i32
                        || new_p.y >= input.height as i32
                        || input.points[..input.part1_cutoff].contains(&new_p)
                    {
                        None
                    } else {
                        Some((new_p, 1))
                    }
                })
                .collect::<Vec<_>>()
        },
        |point| point.manhattan_distance(&end),
        |point| *point == end,
    ) {
        Some((_, cost)) => cost,
        _ => panic!("unsolvable maze"),
    }
}
```

Nice and quick:

```rust
cargo aoc --day 18 --part 1

AOC 2024
Day 18 - Part 1 - v1 : 354
	generator: 116.542µs,
	runner: 6.852792ms
```

### Optimization 1: Using `Grid`

It's already pretty quick, but I think that we can do a *bit* better. For each succession, we're iterating through the `input.points`. Instead, let's go through it once, constructing a `Grid` of walls. 

```rust
#[aoc(day18, part1, v2_grid)]
fn part1_v2_grid(input: &Puzzle) -> i32 {
    let end = (input.width - 1, input.height - 1).into();
    
    let mut grid = Grid::new(input.width, input.height);
    for point in input.points.iter().take(input.part1_cutoff) {
        grid.set(*point, true);
    }

    match pathfinding::prelude::astar(
        &Point::ZERO,
        |&point| {
            Direction::all()
                .iter()
                .filter_map(|d| {
                    let new_p = point + *d;
                    if grid.get(new_p) != Some(&false) {
                        None
                    } else {
                        Some((new_p, 1))
                    }
                })
                .collect::<Vec<_>>()
        },
        |point| point.manhattan_distance(&end),
        |point| *point == end,
    ) {
        Some((_, cost)) => cost,
        _ => panic!("unsolvable maze"),
    }
}
```

The `!= Some(&false)` is because a wall is `Some(&true)` but out of bounds is `None`. For this one, that matters. 

```bash
$ cargo aoc --day 18 --part 1

AOC 2024
Day 18 - Part 1 - v1 : 354
	generator: 116.542µs,
	runner: 6.852792ms

Day 18 - Part 1 - v2_grid : 354
	generator: 93.042µs,
	runner: 480.458µs
```

Woot. 

## Part 2

> What are the coordinates of the first point that, when added, means there is no longer any path from `(0, 0)` to `(70, 70)`?

Oh, now that is more interesting. 

Let's start out the same way:

```rust
#[aoc(day18, part2, v1)]
fn part2_v1(input: &Puzzle) -> String {
    let end = (input.width - 1, input.height - 1).into();

    let p = (input.part1_cutoff..)
        .find_map(|cutoff| {
            match pathfinding::prelude::astar(
                &Point::ZERO,
                |&point| {
                    Direction::all()
                        .iter()
                        .filter_map(|d| {
                            let new_p = point + *d;
                            if new_p.x < 0
                                || new_p.y < 0
                                || new_p.x >= input.width as i32
                                || new_p.y >= input.height as i32
                                || input.points[..cutoff].contains(&new_p)
                            {
                                None
                            } else {
                                Some((new_p, 1))
                            }
                        })
                        .collect::<Vec<_>>()
                },
                |point| point.manhattan_distance(&end),
                |point| *point == end,
            ) {
                Some(_) => None,
                _ => Some(input.points[cutoff - 1]),
            }
        })
        .unwrap();

    format!("{x},{y}", x = p.x, y = p.y)
}
```

This isn't using the `Grid` yet (I wrote `part1_v2_grid` after optimizing `part2`). Other than that, the algorithm is pretty straight forward, I think. Start at the part1 cutoff (since we know that has a solution) and try adding each point. 

```bash
$ cargo aoc --day 18 --part 2

AOC 2024
Day 18 - Part 2 - v1 : 36,17
	generator: 125.958µs,
	runner: 12.51377325s
```

Okay, *that* I know I can do better than. 

Here's what we're working with so far ([script](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/bin/day18-part2-v1-render.rs)):

<video controls src="/embeds/2024/aoc/day18-part2-v1.mp4"></video>

### Optimization 2: Two neighbors

Okay, let's think about the problem statement. We're removing points one by one. Looking at the video above, it appears that we're purposely making a maze with narrow corridors, so I bet we can remove a whole punch of points by always checking if the point we're removing had exactly two neighbors (if it had 3-4, it's too open to be the cutoff point[^ish]; 0-1 means it was already a dead end). 

[^ish]: This isn't actually true in general I don't think, since you can cut off an important 3 or 4 way merge, but for the actual generated input, it works. 

```rust
#[aoc(day18, part2, v2_two_neighbors)]
fn part2_v2_two_neighbors(input: &Puzzle) -> String {
    let end = (input.width - 1, input.height - 1).into();

    let p = (input.part1_cutoff..)
        .find_map(|cutoff| {
            let new_point = input.points[cutoff - 1];

            // To be a cutoff, the new point must have exactly two open neighbors
            if Direction::all()
                .iter()
                .filter(|d| {
                    let new_p = new_point + **d;
                    new_p.x >= 0
                        && new_p.y >= 0
                        && new_p.x < input.width as i32
                        && new_p.y < input.height as i32
                        && !input.points[..cutoff].contains(&new_p)
                })
                .count()
                != 2
            {
                return None;
            }

            match pathfinding::prelude::astar(
                &Point::ZERO,
                |&point| {
                    Direction::all()
                        .iter()
                        .filter_map(|d| {
                            let new_p = point + *d;
                            if new_p.x < 0
                                || new_p.y < 0
                                || new_p.x >= input.width as i32
                                || new_p.y >= input.height as i32
                                || input.points[..cutoff].contains(&new_p)
                            {
                                None
                            } else {
                                Some((new_p, 1))
                            }
                        })
                        .collect::<Vec<_>>()
                },
                |point| point.manhattan_distance(&end),
                |point| *point == end,
            ) {
                Some(_) => None,
                _ => Some(input.points[cutoff - 1]),
            }
        })
        .unwrap();

    format!("{x},{y}", x = p.x, y = p.y)
}
```

I didn't generate a video of this one, since it's the same as [v3 below](#optimization-3-using-grid), but it is quicker!

```bash
$ cargo aoc --day 18 --part 2

AOC 2024
Day 18 - Part 2 - v1 : 36,17
	generator: 125.958µs,
	runner: 12.51377325s

Day 18 - Part 2 - v2_two_neighbors : 36,17
	generator: 104.541µs,
	runner: 4.641415792s
```

### Optimization 3: Using `Grid`

Okay, here's the point where now me caught up to past me. Let's switch all the checks to using `Grid`:

```rust
#[aoc(day18, part2, v3_grid)]
fn part2_v3_grid(input: &Puzzle) -> String {
    let end = (input.width - 1, input.height - 1).into();

    let mut grid = Grid::new(input.width, input.height);
    for p in input.points.iter().take(input.part1_cutoff) {
        grid.set(*p, true);
    }

    let p = (input.part1_cutoff..)
        .find_map(|cutoff| {
            let new_point = input.points[cutoff - 1];
            grid.set(new_point, true);

            // To be a cutoff, the new point must have exactly two open neighbors
            if new_point
                .neighbors()
                .iter()
                .filter(|&p| grid.get(*p) != Some(&false))
                .count()
                != 2
            {
                return None;
            }

            // Verify if the new point *actually* cut us off
            match pathfinding::prelude::astar(
                &Point::ZERO,
                |&point| {
                    Direction::all()
                        .iter()
                        .filter_map(|d| {
                            if grid.get(point + *d) == Some(&false) {
                                Some((point + *d, 1))
                            } else {
                                None
                            }
                        })
                        .collect::<Vec<_>>()
                },
                |point| point.manhattan_distance(&end),
                |point| *point == end,
            ) {
                Some(_) => None,
                _ => Some(input.points[cutoff - 1]),
            }
        })
        .unwrap();

    format!("{x},{y}", x = p.x, y = p.y)
}
```

And that one we get a nice speedup for!

```bash
$ cargo aoc --day 18 --part 2

AOC 2024
Day 18 - Part 2 - v1 : 36,17
	generator: 125.958µs,
	runner: 12.51377325s

Day 18 - Part 2 - v2_two_neighbors : 36,17
	generator: 104.541µs,
	runner: 4.641415792s

Day 18 - Part 2 - v3_grid : 36,17
	generator: 96.417µs,
	runner: 134.909833ms
```

Here's a video of this one ([script](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/bin/day18-part2-v3-render.rs)):

<video controls src="/embeds/2024/aoc/day18-part2-v3.mp4"></video>

And a comparison:

<video controls src="/embeds/2024/aoc/day18-part2-v1-v3.mp4"></video>

### Optimization 4: On the best path

Okay, looking at those, we have (at least) one more trick that we can pull. And better yet, this works in the general case... not just in these puzzle inputs.

Here's the idea: If you remove a point that is *not* on the previously found best path (for the previous list of points), we *know* that this cannot be the point that breaks our graph. It's true for any path (not just the fastest), but it's quicker and more efficient[^worstcast] to remove just the best case anyways. 

[^worstcast]: Technically if a puzzle was constructed to always remove a point on the best path, this would perform worse, since it will always recheck when if it was a point on every path, that wouldn't be a problem. 

```rust
#[aoc(day18, part2, v4_on_best_path)]
fn part2_v4_on_best_path(input: &Puzzle) -> String {
    let end = (input.width - 1, input.height - 1).into();

    let mut grid = Grid::new(input.width, input.height);
    for p in input.points.iter().take(input.part1_cutoff) {
        grid.set(*p, true);
    }

    let mut previous_best_path = None;

    let p = (input.part1_cutoff..input.points.len())
        .find_map(|cutoff| {
            let new_point = input.points[cutoff - 1];
            grid.set(new_point, true);
            
            // To be a cutoff, the new point must have exactly two open neighbors
            if new_point
                .neighbors()
                .iter()
                .filter(|&p| grid.get(*p) != Some(&false))
                .count()
                != 2
            {
                return None;
            }

            // And it must have been on the previous best path (if there was one)
            if previous_best_path
                .as_ref()
                .map_or(false, |path: &Vec<Point>| !path.contains(&new_point))
            {
                return None;
            }

            // Verify if the new point *actually* cut us off
            match pathfinding::prelude::astar(
                &Point::ZERO,
                |&point| {
                    Direction::all()
                        .iter()
                        .filter_map(|d| {
                            if grid.get(point + *d) == Some(&false) {
                                Some((point + *d, 1))
                            } else {
                                None
                            }
                        })
                        .collect::<Vec<_>>()
                },
                |point| point.manhattan_distance(&end),
                |point| *point == end,
            ) {
                Some((path, _)) => {
                    previous_best_path = Some(path);
                    None
                }
                _ => Some(input.points[cutoff - 1]),
            }
        })
        .unwrap();

    format!("{x},{y}", x = p.x, y = p.y)
}
```

And that's it:

```bash
$ cargo aoc --day 18 --part 2

AOC 2024
Day 18 - Part 2 - v1 : 36,17
	generator: 125.958µs,
	runner: 12.51377325s

Day 18 - Part 2 - v2_two_neighbors : 36,17
	generator: 104.541µs,
	runner: 4.641415792s

Day 18 - Part 2 - v3_grid : 36,17
	generator: 96.417µs,
	runner: 134.909833ms

Day 18 - Part 2 - v4_on_best_path : 36,17
	generator: 96.75µs,
	runner: 6.484125ms
```

Another couple orders of magnitude faster!

Here's video of this one ([script](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/bin/day18-part2-v4-render.rs)):

<video controls src="/embeds/2024/aoc/day18-part2-v4.mp4"></video>

And the comparison to [version 3](#optimization-3-using-grid):

<video controls src="/embeds/2024/aoc/day18-part2-v3-v4.mp4"></video>

That... is kind of hilariously faster!

### Optimization 5: Binary search

Okay, let's go a different direction. We know that up until a given point, there is a path and after tha point there is not--with a single point between them. This looks like a candidate for a [[wiki:binary search]]():

```rust
#[aoc(day18, part2, v5_binary)]
fn part2_v5_binary(input: &Puzzle) -> String {
    let end = (input.width - 1, input.height - 1).into();

    let mut lower_bound = input.part1_cutoff;
    let mut upper_bound = input.points.len();

    let mut guess = (lower_bound + upper_bound) / 2;

    loop {
        let mut grid = Grid::new(input.width, input.height);
        for p in input.points.iter().take(guess) {
            grid.set(*p, true);
        }

        match pathfinding::prelude::astar(
            &Point::ZERO,
            |&point| {
                Direction::all()
                    .iter()
                    .filter_map(|d| {
                        if grid.get(point + *d) == Some(&false) {
                            Some((point + *d, 1))
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<_>>()
            },
            |point| point.manhattan_distance(&end),
            |point| *point == end,
        ) {
            Some((_, _)) => {
                if upper_bound - lower_bound <= 1 {
                    break;
                }
                lower_bound = guess;
                guess = (upper_bound + guess) / 2;
            }
            None => {
                if upper_bound - lower_bound <= 1 {
                    break;
                }
                upper_bound = guess;
                guess = (lower_bound + guess) / 2;
            }
        }
    }

    let point = input.points[guess - 1];
    format!("{x},{y}", x = point.x, y = point.y)
}
```

Essentially, start by guessing that we're halfway between the 1024 from part1 and the end of the list. If that has a valid path, cut the distance from there to the end in half and try there. If it doesn't, do the same between 1024 and the guess. Keep going until our bounds only have a single point. 

```bash
$ cargo aoc --day 18 --part 2

AOC 2024
Day 18 - Part 2 - v1 : 36,17
	generator: 125.958µs,
	runner: 12.51377325s

Day 18 - Part 2 - v2_two_neighbors : 36,17
	generator: 104.541µs,
	runner: 4.641415792s

Day 18 - Part 2 - v3_grid : 36,17
	generator: 96.417µs,
	runner: 134.909833ms

Day 18 - Part 2 - v4_on_best_path : 36,17
	generator: 96.75µs,
	runner: 6.484125ms

Day 18 - Part 2 - v5_binary : 24,20
	generator: 102.084µs,
	runner: 852.541µs
```

And we're under 1ms. Woot. 

I think the 'on best path' is a bit more interesting, but the binary search is significantly faster. Given we're searching 3450 maximum points (starting at 1024), we'll need to check on average of $log_2{3450 - 1024} \approx 11$ cases. Pretty quick. :smile:

This one is a bit harder to visualize, but here's a go at it ([script](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/bin/day18-part2-v5-render.rs)):

<video controls src="/embeds/2024/aoc/day18-part2-v5.mp4"></video>

The green points are ones added when jumping forward and the red are those removed when jumping back (until the last frame which has the final path). I slowed it down by 10... otherwise it's just not possible to see much!

## Benchmarks

```bash
$ cargo aoc bench --day 18

Day18 - Part1/v1                time:   [5.9830 ms 6.0103 ms 6.0396 ms]
Day18 - Part1/v2_grid           time:   [380.54 µs 382.55 µs 384.60 µs]
  
Day18 - Part2/v1                time:   [12.393 s  12.441 s  12.489 s]
Day18 - Part2/v2_two_neighbors  time:   [4.4791 s  4.4993 s  4.5201 s]
Day18 - Part2/v3_grid           time:   [134.72 ms 136.76 ms 139.17 ms]
Day18 - Part2/v4_on_best_path   time:   [6.4949 ms 6.5147 ms 6.5355 ms]
Day18 - Part2/v5_binary         time:   [858.19 µs 862.76 µs 867.59 µs]
```

I probably did not need to actually benchmark `Part2/v1`... that took like 20 minutes to run. But it's not like I couldn't go off and do other things (like write this post!) while it ran. 

Onward!