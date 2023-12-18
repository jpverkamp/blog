---
title: "AoC 2023 Day 17: A-Starinator"
date: 2023-12-17 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 17: Clumsy Crucible](https://adventofcode.com/2023/day/17)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day17) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a grid of costs, find the shortest path from top left to bottom right. You may not double back or go straight more than 3 steps in a row. 

<!--more-->

### Types and Parsing

For the most part, we're just using the `Grid` as data store:

```rust
let grid = Grid::read(input.as_str(), |c| c.to_digit(10));
```

I did add a `Direction` `enum` with `North`, `South`, etc variants, a `left()` and `right` method to turn, and converting them into `Point`. 

### Attempts

That *more than 3 in a row* really makes things more interesting. I went through a few different iterations before finally actually just throwing the [`pathfinding` crate](https://docs.rs/pathfinding/latest/pathfinding/) at it.

Things I tried:

* Defining a caching `best_path` function that takes a `Point`, `Direction`, and `count` (how far we've gone in the same direction). Split into the up to three possible cases (left, right, straight if <= 3), recur, and return the best.

    This actually worked pretty well... for the test cases. But I got a pretty major [[wiki:stack overflow]]() when it came to the full test. The main problem is that you can easily loop around, badly ballooning the number of cases. 

* Start at the end and go through once, updating a grid with the best way to get to the next step. Keep iterating this until it stabilizes. 

    This worked well enough... except you need to keep at least two possible 'best' solutions for each square: one in which you go straight (and may hit that limit) and one in which you don't. You can't just store one best, so I never got the best answers. 

* Rewrite the first case (`best_path`) with a better method of filtering out the next cases. This will actually come back. 

### Solution

Okay, so it's a big mess. Backing up a step, what is the actual problem statement? We're looking for a path. The best known way to do [[wiki:pathfinding]]() ... [[wiki:A* search algorithm]](). So let's just see if we can implement that!

Enter the [`pathfinding` crate's `astar` method](https://docs.rs/pathfinding/latest/pathfinding/directed/astar/fn.astar.html). 

To make this work, we need to define:

* A state. This needs to include both the `position` we're at, but also information about facing and how long we've gone in one direction:

```rust
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash, Ord, PartialOrd)]
struct State {
    position: Point,
    direction: Direction,
    count: u32,
}
```

* A `successors` function. Given a `State`, which `States` can we go to next. This is where we deal with running off the map and going more than 3 in a line. 

* A `heuristic` function. This is a guess to getting to the end. This is easy at least, we can just use the [[wiki:manhattan distance]]() for this, it will work well enough. 

* A `success` function. This will define when we're done. Also easy enough. 

So... let's do it?

```rust
let result = astar(
    &State {
        position: Point::new(0, 0),
        direction: South,
        count: 0,
    },
    // successor function
    |&s| {
        [s.direction.left(), s.direction, s.direction.right()]
            .into_iter()
            // Next point must be in bounds
            .filter(|d| grid.bounds.contains(&(s.position + Point::from(*d))))
            // Can't go more than 3 in the same direction
            .filter(|d| s.count < 3 || s.direction != *d)
            // Generate the next state for each neighbor
            .map(|d| State {
                position: s.position + Point::from(d),
                direction: d,
                count: if s.direction == d { s.count + 1 } else { 1 },
            })
            // Add score for each node moved
            .map(|s| (s, *grid.get(&s.position).unwrap()))
            .collect::<Vec<_>>()
    },
    // heuristic function
    |&s| {
        s.position
            .manhattan_distance(&Point::new(grid.bounds.max_x, grid.bounds.max_y))
            as u32
    },
    // goal function
    |&s| s.position.x == grid.bounds.max_x && s.position.y == grid.bounds.max_y,
);
```

The `successor` function is by far the most interesting, but I really like how that ended up in the more functional style. Start with the three possible directions, and then `filter` out problems (out of bounds, going straight more than 3 times), `map` it into a new state, and then add the score for this movement (that's what the tuple is). 

Other than, that, `astar` just does what we need. It returns the path and score:

```rust
// Calculate total score
if let Some((_path, score)) = result {
    println!("{score}");
} else {
    eprintln!("no path found");
}
```

And ... it works great. Feels like cheating, but I've written A* ... a number of times before. I probably could write it again. I think using the tools available is a big part of programming. 

## Part 2

> Instead of moving no more than 3 in a row, you now have to move *at least* 4 before you can turn (or before you reach the final corner) and you cannot move more than 10. 

This almost feels like double cheating, since all I have to do is change the one filter:

```rust
    // ...
    // Must go 4 in a direction before turning
    // Cannot go more than 10 in a direction
    // count == 0 is a special case for the start
    // This count is before the current move
    .filter(|d| {
        s.count == 0
            || (s.count < 4 && s.direction == *d)
            || (s.count >= 4 && s.count <= 10)
    })
    // ...
```

The extra `s.count == 0` is necessary to make sure that the direction we set in our initial `State` doesn't matter. Other than that, we never have a `count == 0`. Theoretically, an `Option` would have been better here (rather than a special case), but that does inject a lot of extra checks. 

My biggest problem was that I originally had only `|| s.count <= 10` on the last line, without thinking that that would completely ignore the line above it. 

Other than that, we have our solution!

## Performance

Still about the same runtime:

```rust
$ just time 17 1

hyperfine --warmup 3 'just run 17 1'
Benchmark 1: just run 17 1
  Time (mean ± σ):     186.0 ms ±  43.6 ms    [User: 71.6 ms, System: 22.6 ms]
  Range (min … max):   144.7 ms … 329.9 ms    15 runs

$ just time 17 2

hyperfine --warmup 3 'just run 17 2'
Benchmark 1: just run 17 2
  Time (mean ± σ):     256.8 ms ±  18.8 ms    [User: 150.5 ms, System: 26.0 ms]
  Range (min … max):   235.6 ms … 293.8 ms    12 runs
```

It would probably be possible to tweak the `heuristic` function a bit to speed that up, but we're already under 1/4 a second (including disk access and parsing), so I don't really feel the need to speed it up any. 

Onward!