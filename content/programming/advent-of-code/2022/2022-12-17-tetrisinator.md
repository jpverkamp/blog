---
title: "AoC 2022 Day 17: Tetrisinator"
date: 2022-12-17 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Games
- Tetris
- Optimization
- Modular Arithmetic
---
## Source: [Pyroclastic Flow](https://adventofcode.com/2022/day/17)

## Part 1

> Simulate {{<wikipedia "Tetris">}} on a 7 wide board with a given (infinitely repeated) series of left and right inputs to be applied on each frame before dropping the block and a given (infinitely repeated) set of blocks. Once 2022 blocks have been dropped, what is the total height of the placed blocks? 

<!--more-->

Sweet!

Let's just directly simulate it, what could go wrong? 

First, the blocks:

```rust
#[derive(Debug)]
struct Rock {
    points: Vec<Point>,
}

impl Rock {
    fn nth(n: usize) -> Rock {
        match n % 5 {
            0 => Rock {
                points: vec![
                    Point { x: 0, y: 0 },
                    Point { x: 1, y: 0 },
                    Point { x: 2, y: 0 },
                    Point { x: 3, y: 0 },
                ],
            },
            1 => Rock {
                points: vec![
                    Point { x: 1, y: 0 },
                    Point { x: 0, y: 1 },
                    Point { x: 1, y: 1 },
                    Point { x: 2, y: 1 },
                    Point { x: 1, y: 2 },
                ],
            },
            2 => Rock {
                points: vec![
                    Point { x: 0, y: 0 },
                    Point { x: 1, y: 0 },
                    Point { x: 2, y: 0 },
                    Point { x: 2, y: 1 },
                    Point { x: 2, y: 2 },
                ],
            },
            3 => Rock {
                points: vec![
                    Point { x: 0, y: 0 },
                    Point { x: 0, y: 1 },
                    Point { x: 0, y: 2 },
                    Point { x: 0, y: 3 },
                ],
            },
            4 => Rock {
                points: vec![
                    Point { x: 0, y: 0 },
                    Point { x: 1, y: 0 },
                    Point { x: 0, y: 1 },
                    Point { x: 1, y: 1 },
                ],
            },
            _ => panic!("n % 5 somehow not 0..=4"),
        }
    }
}
```

We always have the same 5 blocks, so `nth` will use {{<wikipedia "modular arithmetic">}} to figure out which block we need. One gotcha is that we need the same anchor point on each block so that we can correctly spawn them on the map. In this case, that is the bottom left. 

After that, the map:

```rust
#[derive(Debug)]
struct Map {
    width: usize,
    tower_height: usize,

    walls: HashSet<Point>,

    rock_count: usize,
    next_rock: usize,
    rock: Rock,
    rock_at: Point,
}

impl Map {
    fn new(width: usize) -> Self {
        let mut walls = HashSet::new();
        for x in 0..=(width + 2) {
            walls.insert(Point {
                x: x as isize,
                y: 0,
            });
        }
        for y in 0..=4 {
            walls.insert(Point {
                x: 0,
                y: y as isize,
            });
            walls.insert(Point {
                x: 1 + width as isize,
                y: y as isize,
            });
        }

        Map {
            width,
            tower_height: 0,
            walls,
            rock_count: 0,
            rock: Rock::nth(0),
            rock_at: Point {
                x: 3,
                y: 4 as isize,
            },
        }
    }
}
```

We are going to keep the `walls` as a `HashSet` of `Point`. This should be fast enough for collision detection, we just have to make sure we keep extending it upwards. 

Other than that:
 * `width` is the constant width
 * `tower_height` is the current highest `y` value of any wall (to save iterating through `walls`)
 * `rock_count` is how many rocks we've spawned so far so we know when to stop
 * `rock` is the current rock being dropped
 * `rock_at` is the offset where that rock is

After that, we want a function that can simulate one step, given the input (we'll come back to how we parse that in a bit):

```rust
impl Map {
    fn step(&mut self, xd: isize) {
        // Try to move left/right
        // If we can't, just don't move
        let sidestep = Point { x: xd, y: 0 };
        if !self
            .rock
            .points
            .iter()
            .any(|p| self.walls.contains(&(*p + self.rock_at + sidestep)))
        {
            self.rock_at = self.rock_at + sidestep;
        }

        // Try to move down
        // If we can't, lock in place
        let downstep = Point { x: 0, y: -1 };
        if self
            .rock
            .points
            .iter()
            .any(|p| self.walls.contains(&(*p + self.rock_at + downstep)))
        {
            self.lock_and_spawn();
        } else {
            self.rock_at = self.rock_at + downstep;
        }
    }
}
```

I do love the functional style code. In this case, we'll first `sidestep` left or right. If any of the rock points (offset by `rock_at` and then `sidestep`) touch any of the walls, just don't do this move. Then, do the same with a `downstep`, but if we have any collisions this time, `lock_and_spawn` the current and a new rock:

```rust
impl Map {
    fn lock_and_spawn(&mut self) {
        for p in self.rock.points.iter() {
            let p = *p + self.rock_at;
            self.tower_height = self.tower_height.max(p.y as usize);
            self.walls.insert(p);
        }

        // Inefficient, but :shrug:
        for y in 0..=(self.tower_height + 10) {
            self.walls.insert(Point {
                x: 0,
                y: y as isize,
            });
            self.walls.insert(Point {
                x: 1 + self.width as isize,
                y: y as isize,
            });
        }

        // Don't forget the extra offset for the left wall and floor
        self.rock = Rock::nth(self.current_rock);
        self.rock_at = Point {
            x: 1 + 2,
            y: 1 + 3 + self.tower_height as isize,
        };

        self.rock_count += 1;
    }
}
```

This one is interesting. It a nutshell:

* turn the rock into walls, updating the `tower_height`
* expand the walls well beyond that height, just in case (we're reinserting all previous walls, but :shrug:, it works for this part)
* spawning the next new rock at 2 from the left wall and 3 from the tallest block
* increment which rock we're on

And... that's it!

```rust
fn part1(filename: &Path) -> String {
    let lines = read_lines(filename);
    let winds = lines[0].as_bytes();

    // Create a custom infinite iterator for the wind
    let mut first = true;
    let mut index = 0;
    let mut wind_iter = std::iter::from_fn(move || {
        if first {
            first = false;
        } else {
            index += 1;
        }
        Some(winds[index % winds.len()] as char)
    });

    // Build a new map and iterate until we hit the target
    let mut map = Map::new(7);
    loop {
        match wind_iter.next() {
            Some('<') => {
                map.step(-1);
            }
            Some('>') => {
                map.step(1);
            }
            _ => panic!("unexpected char in wind_iter"),
        }

        if map.rock_count >= 2022 {
            break;
        }
    }

    map.tower_height.to_string()
}
```

Okay, not quite. We still need a way to make an infinite iterator of the wind / moves left and right. That's where [`std::iter::from_fn`](https://doc.rust-lang.org/std/iter/fn.from_fn.html) comes in. Basically, it turns a function into an `Iterator`. Keep the state (`index`) and we have it. This would be easier with `generators` (not in stable yet) or making my own struct that implements `Iterator`, but this works well enough. 

Onward!

## Part 2

> Do the same thing for 1 trillion blocks. 

I enjoy problems like this. Yes, you could just simulate the first bit. But... that's going to take days at best (given my `122 ms` for part 1, the estimate is just under 700 days and that's assuming constant performance and memory consumption). 

So... we have to do better. 

Idea: the same 6 blocks repeat over and over again, as does the same inputs. So at some point... have to get a cycle, right? Where the blocks are placed in the same way with a relative offset? 

Let's assume that's true:

```rust
fn part2(filename: &Path) -> String {
    let lines = read_lines(filename);
    let winds = lines[0].as_bytes();

    let target: usize = 1000000000000;

    let mut first = true;
    let mut index = 0;
    let mut wind_iter = std::iter::from_fn(move || {
        if first {
            first = false;
        } else {
            index += 1;
        }
        Some(winds[index % winds.len()] as char)
    });

    let mut map = Map::new(7);
    let mut last_rock_count = usize::MAX;
    let mut last_height = 0;
    let mut deltas = Vec::new();

    // Attempt to detect cycles in the delta between heights
    #[derive(Debug)]
    struct Cycle {
        length: usize,
        value: usize,
    }
    let mut cycle = None;

    // Loop until we find a cycle
    // Then loop until the current height and the target are at the same point in the cycle
    // Then add enough cycles to jump ahead to the end
    'cycle: loop {
        match wind_iter.next() {
            Some('<') => {
                map.step(-1);
            }
            Some('>') => {
                map.step(1);
            }
            _ => panic!("unexpected char in wind_iter"),
        }

        // Update the count and height as before, but also calculate delta (change in height)
        if map.rock_count != last_rock_count {
            let count = map.rock_count;
            let height = map.tower_height;
            let delta = height - last_height;
            deltas.push(delta);

            if cfg!(debug_assertions) {
                println!("{count}\t{delta}\t{height}");
            }

            last_rock_count = count;
            last_height = height;

            // Try to detect cycles in delta by:
            // - for each length from a small value up to the full list
            // - test if [prefix][data of length][data of length] repeats the data sections
            // Once we've detected a cycle, stop looking for one (but keep iterating)
            // The offsets are completely random at this point, I'm not sure what to base it off
            if cycle.is_none() && deltas.len() > 2000 {
                for length in 1000..(deltas.len() / 2) {
                    let seq1 = deltas.iter().rev().take(length).collect::<Vec<_>>();
                    let seq2 = deltas
                        .iter()
                        .rev()
                        .skip(length)
                        .take(length)
                        .collect::<Vec<_>>();

                    if seq1 == seq2 {
                        cycle = Some(Cycle {
                            length: length,
                            value: seq1.into_iter().sum::<usize>(),
                        });

                        if cfg!(debug_assertions) {
                            println!("cycle detected: {cycle:?}");
                        }
                    }
                }
            }

            // If we have a cycle, we need the current rock and the target to be at the same offset
            // Otherwise we'd have to add partial cycles; we can do it, this is just easier
            match cycle {
                Some(Cycle { length, value, .. }) => {
                    if map.rock_count % length == target % length {
                        // Hacky, but technically correct? Doesn't update walls
                        // We certainly could, but no point for this problem
                        let jumps = (target - map.rock_count) / length;
                        map.rock_count += jumps * length;
                        map.tower_height += jumps * value;
                        break 'cycle;
                    }
                }
                _ => {}
            }
        }

        // Edge case: If we never found a cycle but hit the target anyways, be done
        if map.rock_count >= target {
            break 'cycle;
        }
    }

    map.tower_height.to_string()
}
```

To detect the cycle, I'm not looking at the heights, but rather the `deltas` between the heights. The height is always increasing, but the `deltas` should fall into a pattern eventually. 

The main interesting part is the cycle detection:

```rust
// Try to detect cycles in delta by:
// - for each length from a small value up to the full list
// - test if [prefix][data of length][data of length] repeats the data sections
// Once we've detected a cycle, stop looking for one (but keep iterating)
// The offsets are completely random at this point, I'm not sure what to base it off
if cycle.is_none() && deltas.len() > 2000 {
    for length in 1000..(deltas.len() / 2) {
        let seq1 = deltas.iter().rev().take(length).collect::<Vec<_>>();
        let seq2 = deltas
            .iter()
            .rev()
            .skip(length)
            .take(length)
            .collect::<Vec<_>>();

        if seq1 == seq2 {
            cycle = Some(Cycle {
                length: length,
                value: seq1.into_iter().sum::<usize>(),
            });

            if cfg!(debug_assertions) {
                println!("cycle detected: {cycle:?}");
            }
        }
    }
}
```

I expect there are smarter algorithms for this (at the very least ones that don't need to create two `iter()` and `skip()` over the elements for the second one. But this does at least make sense. So far as the lower bound `1000` on length... it's totally a made up number that at least for this works. It can't be too short or you risk false positives. 

Plus, generated all of the `delta` values up to 10,000 or so, copied a random section and replaced it with `$section\n`. That actually showed me the cycle I was looking for, which happened to be 1740 characters long. So I knew this would catch it. 

Another gotcha was originally the possibility of something that repeated twice but not thrice. So I had at times a `seq3` generated the same way albeit with `.skip(2 * length)`, but it turned out not to be necessary. 

The other interesting bit is that once we've found a cycle, we can't jump immediately. Instead, we have to wait until the current place in that cycle 'lines up' with the target we're aiming for. As I mention in the comment, we could have instead added a slice of `deltas`, but I found this easier. Just use `%` (modulo) again until `map.rock_count` and `target` are an even multiple of `cycle.length` apart and bam. Jump to the end. One trillion blocks dropped stretching 1.54 trillion blocks high in a second and change. Not bad at all. 

### A cleanup side note

One final aside, I did momentarily go down a variant where I only kept part of the board in memory at any given time:

```rust
impl Map {
    // A currently unneeded function used to remove all walls lower than a certain threshold
    // We'll never collide with them anyways
    // Unfortunately, the drain_filter function that would have made this more performant isn't in stable
    #[allow(dead_code)]
    fn cleanup(&mut self, threshold: usize) {
        self.walls = self
            .walls
            .iter()
            .filter_map(|p| {
                if p.y >= (self.tower_height - threshold) as isize {
                    Some(*p)
                } else {
                    None
                }
            })
            .collect::<HashSet<_>>();
    }
}
```

This had the advantage of making the initial part (before we find a cycle) potentially faster since we have to compare again fewer `walls`. But it turns out that `HashSet::contains` is super faster and we didn't run out of RAM... so I ended up not using it. It's more expensive to remove the elements than just to keep them all along. I did tree a `BTreeSet` as well, which should have better `.pop()` performance, but that requires correctly ordering the points. Which I could do... but this is fast enough. 

## Performance

Speaking of which:

```bash
$ ./target/release/17-tetrisnator 1 data/17.txt

3114
took 122.644416ms

$ ./target/release/17-tetrisnator 2 data/17.txt

1540804597682
took 1.472870625s
```

We're over a second now, mostly because I didn't 