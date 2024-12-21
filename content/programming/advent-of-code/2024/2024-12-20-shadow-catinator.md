---
title: "AoC 2024 Day 20: Shadow Catinator"
date: 2024-12-20 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics: 
- Pathfinding
- A-Star
- Dijkstra's Algorithm
---
## Source: [Day 20: Race Condition](https://adventofcode.com/2024/day/20)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day20.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a maze with exactly one path, find how many single walls you can walk through (remove) that shorten the best path by at least 100 units. 

<!--more-->

Well this one was quite the ride. 

I went quite down the rabbit hole on a really cool (in my opinion) solution before realizing I was missing a few things and badly overestimating how much work I needed to do for this problem. Then a number of times, I had [[wiki:off by one errors]]() and incorrect inequalities. Oy. I really could have done better with test cases, but it's a tricky one to write for. 

### Version 1: Entirely over complicated...

Okay, first version (that never did finish; it works on the examples, but not sure about the full puzzle). 

The basic idea: 

* Find the length of the best path using [[wiki:A* search]]()
* Repeatedly:
  * Run A* with a modified successors function that takes both the point and a state machine
    * If we're in the starting state, we can move or start skipping
    * If we're skipping, we can continue the skip
    * If we're done skipping, we can never skip again
  * Once that returns, you have a new valid skip; store that so that the above A* cannot finish a skip with the same list

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum State {
    PreSkip,
    Skip0,
    Skip1(Point),
    PostSkip(Point),
    NoSkip,
}

// This works in theory but is *very very slow* on the main input
#[aoc(day20, part1, v1)]
fn part1_v1(input: &Puzzle) -> usize {
    // Keep track of skips we've used
    // We cannot use the same one more than once
    let applied_skips = Rc::new(RefCell::new(HashSet::new()));

    // Shared successor function, combining the point we're at and the state we're in

    let successor = |(point, state): &(Point, State)| {
        let mut successors = Vec::new();

        // If we're pre-skip, we can always start the skip
        // Do not include the move as part of this
        if *state == State::PreSkip {
            successors.push(((*point, State::Skip0), 0));
        }

        // If we're out of skip points, transition to post skip without moving
        // This means there are *no more cases*
        // Also, we can't skip the exact same set of walls more than once
        if let State::Skip1(p1) = state {
            if !applied_skips.borrow().contains(p1) {
                successors.push(((*point, State::PostSkip(*p1)), 0));
            }
            return successors;
        }

        // Try to move in each direction
        // If we're in a skip state, we can ignore walls
        Direction::all()
            .iter()
            .map(|&dir| (*point + dir, *state))
            .for_each(|(new_point, state)| {
                // We can never walk off the edge of the map
                if input.walls.get(new_point).is_none() {
                    return;
                }

                match state {
                    // Pre-skip, post-skip, and no-skip states have to obey walls
                    State::PreSkip | State::PostSkip(_) | State::NoSkip => {
                        if input.walls.get(new_point) == Some(&false) {
                            successors.push(((new_point, state), 1));
                        }
                    }

                    // Skip means we can only walk on walls
                    State::Skip0 => {
                        successors.push(((new_point, State::Skip1(new_point)), 1));
                    }
                    // Skip 2 should not be evalulate here
                    State::Skip1(_) => unreachable!("Skip1 should not be evaluated here"),
                }
            });

        successors
    };

    // The initial time doesn't include skipping, so use the NoSkip state
    let initial_time = match astar(
        &(input.start, State::NoSkip),
        successor,
        |(point, _)| point.manhattan_distance(&input.end) as u32,
        |(point, _)| point == &input.end,
    ) {
        Some((_path, cost)) => cost,
        None => panic!("No initial path found"),
    };

    // Keep going so long as we find 'cheating' skips
    while let Some((path, cost)) = astar(
        &(input.start, State::PreSkip),
        successor,
        |(point, _)| point.manhattan_distance(&input.end) as u32,
        |(point, state)| point == &input.end && matches!(state, State::PostSkip(_)),
    ) {
        // The last point on the path stores the skip we used
        let last_state = path.last().unwrap().1;
        let skip_used = match last_state {
            State::PostSkip(p) => p,
            _ => {
                unreachable!("We should have ended in a post-skip state, was in {last_state:?}")
            }
        };

        // How much time did we save?
        let savings = initial_time - cost;

        // If we didn't save enough time (or any time!), we're done
        if savings < if input.example { 1 } else { 100 } {
            break;
        }

        // We have a new skip, so store that we used it
        applied_skips.borrow_mut().insert(skip_used);
    }

    let result = applied_skips.borrow().len();
    result
}
```

That... is bonkers code, but I worked on it for a while and I wanted to share it. I have no idea if it would ever finish, I expect I'd have errors anyways...

### Version 2: Floodfill

Okay, now I actually *looked* at the puzzle input. It's a very tight maze. 

So option 2 was to perform a floodfill, start at the first point and flood outwards. At each point, try to go across a wall[^wall]. If you haven't had a shortcut to that point yet, include it!

[^wall]: One of the skips here is that because you're skipping across a single point, you can never cut off corners, it always has to be a straight line. 

```rust
// This doesn't work because it doesn't account for the skip bound
#[aoc(day20, part1, floodfill)]
fn part1_floodfill(input: &Puzzle) -> usize {
    let mut point = input.start;
    let mut visited = Grid::new(input.walls.width, input.walls.height);
    let mut skipped = HashSet::new();
    let mut shortcuts = 0;

    'next_point: loop {
        visited.set(point, true);

        // Are there any walls that we can skip that will lead us back on to the path
        // It has to be straight two steps, otherwise it will end up the same length
        // (We'd be cutting off a corner)
        for d in Direction::all() {
            if input.walls.get(point + d) == Some(&true)
                && input.walls.get(point + d + d) == Some(&false)
                && !visited.get(point + d + d).unwrap_or(&false)
                && !skipped.contains(&(point + d, point + d + d))
            {
                // Can only skip the same point once
                skipped.insert((point + d, point + d + d));

                shortcuts += 1;
            }
        }

        // If we're at the end, stop
        if point == input.end {
            break;
        }

        // Otherwise, find the one point that we've not already visited
        for d in Direction::all() {
            if input.walls.get(point + d) == Some(&false)
                && !visited.get(point + d).unwrap_or(&false)
            {
                point = point + d;
                continue 'next_point;
            }
        }

        // If we make it here, we failed to find the path
        unreachable!("No path found at {point:?}");
    }

    shortcuts
}
```

The problem with this is that (for some reason :p) we don't actually want the entire count of these, we only want those that cut off at least 100 steps. Which... this algorithm has no good way of calculating. I could run A* from the far point each time... but when working on that, I was already thinking of the next solution!

### Version 3: Directly scan along the path

Okay, the first actually working version for part1!

And so far as actually reading the problem... turns out there was one *very* important bit of that:

> Because there is **only a single path** from the start to the end and the programs all go the same speed, the races used to be pretty boring.

Emphasis mine. 

So what we can do is find that best path. Because of the structure of the input, we actually find that all possible shortcuts are on this path. I'm not **100%** sure that you can actually generally say that... at least if it's possible to have deadends you can cut over to. But since that's not the case, you'll always cut from a point on this path to another point on the path!

So, now we scan the path, then for each point it, we try each wall, will going in that direction (once again ignoring corners) lead to a point further along the path? (As opposed to before us). 

```rust
#[aoc(day20, part1, pathscan)]
fn part1_pathscan(input: &Puzzle) -> usize {
    // First, find the one true path
    let path = astar(
        &input.start,
        |point| {
            Direction::all()
                .iter()
                .map(|&dir| *point + dir)
                .filter(|&new_point| input.walls.get(new_point) == Some(&false))
                .map(|new_point| (new_point, 1))
                .collect::<Vec<_>>()
        },
        |point| point.manhattan_distance(&input.end),
        |point| *point == input.end,
    )
    .expect("No path found")
    .0;

    let cutoff = if input.example { 1 } else { 100 };

    // Now, for each point in that path, see if we can skip to a point further along the path
    let mut shortcut_count = 0;
    for (i, p) in path.iter().enumerate() {
        // Are there any walls that we can skip that will lead us back on to the path
        // It has to be straight two steps, otherwise it will end up the same length
        // (We'd be cutting off a corner)
        for d in Direction::all() {
            if input.walls.get(*p + d) == Some(&true)
                && input.walls.get(*p + d + d) == Some(&false)
                && path
                    .iter()
                    .position(|&p2| p2 == *p + d + d)
                    .is_some_and(|i2| i2 > i && i2 - i > cutoff)
            {
                shortcut_count += 1;
            }
        }
    }

    shortcut_count
}
```

And here, finally, we have a solution!

```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 1 - pathscan : 1399
	generator: 158.916µs,
	runner: 36.663209ms
```

Now that's already fairly quick, but I think that I have a little bit of room to do better. 

### Optimization 1: Calculate distances once (Dijkstra's algorithm)

First optimization, we are currently doing a bunch of vector scanning to figure out how much space we've saved. We can beat that by using [[wiki:Dijkstra's algorithm]]() to pre-calculate how far each point is from the end and directly know how much we're saving:

```rust
#[aoc(day20, part1, dijkstra)]
fn part1_dijkstra(input: &Puzzle) -> usize {
    // Find every point's distance to the end using dijkstra's algorithm
    let distances = dijkstra_all(&input.end, |point| {
        Direction::all()
            .iter()
            .map(|&dir| *point + dir)
            .filter(|&new_point| input.walls.get(new_point) == Some(&false))
            .map(|new_point| (new_point, 1))
            .collect::<Vec<_>>()
    });

    let cutoff = if input.example { 1 } else { 100 };
    let mut p = input.start;
    let mut shortcut_count = 0;

    // Follow the shortest path via dijkstra's algorithm
    while let Some((next_point, current_distance)) = distances.get(&p) {
        // Are there any walls that we can skip that will lead us back on to the path
        // It has to be straight two steps, otherwise it will end up the same length
        // (We'd be cutting off a corner)
        for d in Direction::all() {
            if input.walls.get(p + d) == Some(&true) && input.walls.get(p + d + d) == Some(&false) {
                // Special case the exit (it's not in the distances map)
                if p + d + d == input.end {
                    shortcut_count += 1;
                    continue;
                }

                // For all other cases, calculate up how much we're saving
                match distances.get(&(p + d + d)) {
                    Some((_, new_distance)) if *new_distance > current_distance + cutoff => {
                        shortcut_count += 1;
                    }
                    _ => {}
                }
            }
        }

        // Advance along dijkstra's path
        p = *next_point;
    }

    shortcut_count
}
```

Not that complicated a change and:

```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 1 - pathscan : 1399
	generator: 158.916µs,
	runner: 36.663209ms
    
Day 20 - Part 1 - dijkstra : 1382
	generator: 112.125µs,
	runner: 4.388792ms
```

It also is significantly faster!

### Optimization 2: Store distances in a `Grid`

But there is still room for just a *bit* of optimization. Dijkstra's still requires hashing each of the points to figure out where on the path we are. We've already found in previous days that we can get a speedup by flattening that into direct access in a `Grid`:

```rust
#[aoc(day20, part1, grid)]
fn part1_grid(input: &Puzzle) -> usize {
    // First, find the one true path
    let path = astar(
        &input.start,
        |point| {
            Direction::all()
                .iter()
                .map(|&dir| *point + dir)
                .filter(|&new_point| input.walls.get(new_point) == Some(&false))
                .map(|new_point| (new_point, 1))
                .collect::<Vec<_>>()
        },
        |point| point.manhattan_distance(&input.end),
        |point| *point == input.end,
    )
    .expect("No path found")
    .0;

    // Store distances as a grid
    let mut distances = Grid::new(input.walls.width, input.walls.height);
    for (i, p) in path.iter().enumerate() {
        distances.set(*p, i);
    }

    let cutoff = if input.example { 1 } else { 100 };

    // Now, for each point in that path, see if we can skip to a point further along the path
    let mut shortcut_count = 0;
    for (i, p) in path.iter().enumerate() {
        // Are there any walls that we can skip that will lead us back on to the path
        // It has to be straight two steps, otherwise it will end up the same length
        // (We'd be cutting off a corner)
        for d in Direction::all() {
            if input.walls.get(*p + d) == Some(&true)
                && input.walls.get(*p + d + d) == Some(&false)
                && distances
                    .get(*p + d + d)
                    .map_or(false, |i2| *i2 > i + cutoff)
            {
                shortcut_count += 1;
            }
        }
    }

    shortcut_count
}
```

And we get just a bit of speedup from that:

```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 1 - pathscan : 1399
	generator: 158.916µs,
	runner: 36.663209ms
    
Day 20 - Part 1 - dijkstra : 1382
	generator: 112.125µs,
	runner: 4.388792ms

Day 20 - Part 1 - grid : 1399
	generator: 66.25µs,
	runner: 2.931375ms
```

And... I think that's probably enough for a moment. I'm not quite in the sub millisecond range (man, I used to go for sub 1 second, or even 1 minute!), but that's still pretty crazy fast. 

(Plus, when I actually do the benchmarking, it *is* submillisecond. 633.33 µs :smile:)

### Pretty pictures

Okay, let's look at what this algorithm is actually doing:

<video controls src="/embeds/2024/aoc/day20-part1.mp4"></video>

What you're seeing is the point following the path, scanning each point around it. If it's a valid skip, it will get saved in green, if not it will flash red but otherwise be skipped.

The acceleration here is not actually part of the image, it's just a really long path. :smile:

## Part 2

> Allow skips of up to 20 spaces. Unique skips are identified by the start and end point (both on the path), different skips with the same start and end are considered the same. How many skips are there now? 

Okay, now that's a complicated!

Luckily, I ended up on a pretty decent algorithm the first time around with caching the distances. 

```rust
#[aoc(day20, part2, pathscan)]
fn part2_pathscan(input: &Puzzle) -> usize {
    let skiplength = 20_i32;
    let cutoff = if input.example { 50 } else { 100 };

    // First, find the one true path
    let path = astar(
        &input.start,
        |point| {
            Direction::all()
                .iter()
                .map(|&dir| *point + dir)
                .filter(|&new_point| input.walls.get(new_point) == Some(&false))
                .map(|new_point| (new_point, 1))
                .collect::<Vec<_>>()
        },
        |point| point.manhattan_distance(&input.end),
        |point| *point == input.end,
    )
    .expect("No path found")
    .0;

    // Find the distance from the exit to every point
    // This will be used to verify 'better' paths
    // We need this because it's possible to take a shortcut to a previous dead end
    let mut distances = dijkstra_all(&input.end, |point| {
        Direction::all()
            .iter()
            .map(|&dir| *point + dir)
            .filter(|&new_point| input.walls.get(new_point) == Some(&false))
            .map(|new_point| (new_point, 1))
            .collect::<Vec<_>>()
    });

    // Add the exit :)
    distances.insert(input.end, (input.end, 0));

    // Now, for each point in that path, see if we can skip to a point further along the path
    // We can skip up to 20, so any point that within manhattan distance 20 is valid
    let mut shortcut_count = 0;
    for (i, p) in path.iter().enumerate() {
        // Are there any walls that we can skip that will lead us back on to the path
        // It has to be straight two steps, otherwise it will end up the same length
        // (We'd be cutting off a corner)
        for xd in -skiplength..=skiplength {
            for yd in -skiplength..=skiplength {
                // Ignore skipping to yourself or skipping too far
                if xd == 0 && yd == 0 || xd.abs() + yd.abs() > skiplength {
                    continue;
                }

                let d: Point = (xd, yd).into();
                let p2: Point = *p + d;

                // Cannot end on a wall
                // This is covered by the distanced map, but this lookup is faster
                // With: 112.44 ms, Without: 189.61 ms
                if input.walls.get(p2) != Some(&false) {
                    continue;
                }

                // Cannot get from the target to the end
                if !distances.contains_key(&p2) {
                    continue;
                }

                // The distance using the shortcut
                let new_distance = i // To start
                    + d.manhattan_distance(&Point::ZERO) as usize // Shortcut
                    + distances.get(&p2).unwrap().1 as usize // To end
                    + 1;

                // Doesn't cut off enough
                if new_distance > path.len() - cutoff {
                    continue;
                }

                // If we've made it this far, we can shortcut!
                shortcut_count += 1;
            }
        }
    }

    shortcut_count
}
```

This time, we do have a few more cases to check, but the core is the same. For each point, we're going to scan out to a [[wiki:Manhattan distance]]() of 20. For each of those points, we have to make sure we're not in a wall, we have a path to the end (this should always be true, since there aren't branches), and the distance is within the cutoff. 

One interesting thing is that we don't actually have to care about unique paths at all! Since we're scanning each exit point exactly once... there's no way for it possibly to have duplicates. I had code for a while that checked that, but when optimizing imagine my amusement realizing it was completely unnecessary. 

```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 2 - pathscan : 994807
	generator: 31.125µs,
	runner: 110.209833ms
```

### Optimization 3: Store distances in a `Grid`

The one optimization I'll do for this one (I spent a lot more on the [rendering](#prettier-pictures)) is once again using `Grid` instead of `HashMap` for the distances. 

Since it's basically the same change and doesn't change the algorithm at all, I'm not going to include the code here, but you can see it [on github](https://github.com/jpverkamp/advent-of-code/blob/47a31aa60a307cd8913cb80db3a742341d3aad3e/2024/src/day20.rs#L461-L544) if you are curious.

And how's it do?

```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 2 - pathscan : 994807
	generator: 31.125µs,
	runner: 110.209833ms

Day 20 - Part 2 - griddist : 4712224
	generator: 62.625µs,
	runner: 38.130625ms
```

There are *a lot* more lookups this time around, so that's a fairly dramatic speedup from not having to hash. 

Onward!

### Optimization 4: Inverting the loop

Okay, a bit later, one final way to look at the problem. 

Very specifically, because we know that there is only one path and every point is on the path, instead of searching from each point out to a radius of 20, instead, we can:

* From each point on the path:
  * For each point starting 100 after that point:
    * If the two points are within 20 of each other AND at least 100 better overall

We still need to find the best path and all the distance to each point and it's really dependent on the structure of the problem, but it turns out that it's got a slightly better constant on the runtime. 

If you want to write it with iters:

```rust
#[aoc(day20, part2, listiter)]
fn part2_listiter(input: &Puzzle) -> usize {
    // ...

    // For any point on the path, for any point at least cutoff further along the path
    // If those two points are within skip_length, there is a shortcut between them
    path.iter()
        .enumerate()
        .map(|(start, p1)| {
            path.iter()
                .skip(start + cutoff)
                .filter(|p2| {
                    // The skip is short enough + the distance saved is big enough
                    p1.manhattan_distance(p2) <= skip_length
                        && distances.get(*p1).unwrap()
                            - distances.get(**p2).unwrap()
                            - p1.manhattan_distance(p2)
                            >= cutoff as i32
                })
                .count()
        })
        .sum::<usize>()
}
```

And if you want to write it with nested for loops:

```rust
#[aoc(day20, part2, listfor)]
fn part2_listfor(input: &Puzzle) -> usize {
    // ...

    // For any point on the path, for any point at least cutoff further along the path
    // If those two points are within skip_length, there is a shortcut between them
    let mut shortcut_count = 0;

    for (start, p1) in path.iter().enumerate() {
        for p2 in path.iter().skip(start + cutoff) {
            // The skip is short enough + the distance saved is big enough
            if p1.manhattan_distance(p2) <= skip_length
                && distances.get(*p1).unwrap()
                    - distances.get(*p2).unwrap()
                    - p1.manhattan_distance(p2)
                    >= cutoff as i32
            {
                shortcut_count += 1;
            }
        }
    }

    shortcut_count
}
```

And they do perform *slightly* quicker:


```bash 
$ cargo aoc --day 20 --part 1

AOC 2024
Day 20 - Part 2 - pathscan : 994807
	generator: 31.125µs,
	runner: 110.209833ms

Day 20 - Part 2 - griddist : 4712224
	generator: 62.625µs,
	runner: 38.130625ms

Day 20 - Part 2 - listiter : 994807
	generator: 30.25µs,
	runner: 30.332125ms

Day 20 - Part 2 - listfor : 994807
	generator: 62.625µs,
	runner: 23.924083ms
```

### Prettier pictures

Okay, rendering time. I had quite a time getting something both interesting and in a reasonable time/filesize:

<video controls src="/embeds/2024/aoc/day20-part2.mp4"></video>

This time, you're not seeing the shortcuts themselves (since I never actually calculate those paths) but instead how many possible shortcuts end at each point as a heatmap (from blue to red).

The white point is where we are scanning and the green diamond is the radius we're looking for shortcut exits in. 

Pretty cool. 

## Benchmarks

```
$ cargo aoc bench --day 20

Day20 - Part1/pathscan  time:   [28.508 ms 28.768 ms 29.124 ms]
Day20 - Part1/dijkstra  time:   [1.2037 ms 1.2152 ms 1.2269 ms]
Day20 - Part1/grid      time:   [627.17 µs 633.33 µs 641.92 µs]

Day20 - Part2/pathscan  time:   [113.84 ms 114.70 ms 115.77 ms]
Day20 - Part2/griddist  time:   [34.101 ms 34.353 ms 34.697 ms]
Day20 - Part2/listiter  time:   [30.221 ms 30.579 ms 31.203 ms]
Day20 - Part2/listfor   time:   [22.468 ms 22.921 ms 23.492 ms]
```

None too shabby. I spent... more time than I care to admit on this one. But it was a fun one, so it goes!