---
title: "AoC 2023 Day 23: Looong Mazinator"
date: 2023-12-23 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 23: A Long Walk](https://adventofcode.com/2023/day/23)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day23) for today (spoilers!)

{{<toc>}}

## Part 1

> Find the longest non-overlapping path through a maze with walls (`#`) and one way paths (`^v<>`). 

<!--more-->

Don't even need types or parsing this time, just use `Grid`:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let grid = Grid::read(input.as_str(), |c| match c {
        '#' => Some(Object::Wall),
        '^' => Some(Object::Slope(Slope::North)),
        'v' => Some(Object::Slope(Slope::South)),
        '>' => Some(Object::Slope(Slope::East)),
        '<' => Some(Object::Slope(Slope::West)),
        _ => None,
    });

    #[derive(Debug)]
    struct State {
        position: Point,
        path: Vec<Point>,
    }

    let mut queue = Vec::new();
    queue.push(State {
        position: Point::new(1, 0),
        path: Vec::with_capacity(1024),
    });

    let mut complete = Vec::new();

    while let Some(state) = queue.pop() {
        for direction in &[
            Point::new(0, 1),
            Point::new(0, -1),
            Point::new(1, 0),
            Point::new(-1, 0),
        ] {
            let next_position = state.position + *direction;

            // If we're at the exit, we've found a complete path
            if next_position == Point::new(grid.bounds.max_x - 1, grid.bounds.max_y) {
                complete.push(state.path.clone());
                continue;
            }

            // If we're out of bounds, we've found an invalid path
            if !grid.bounds.contains(&next_position) {
                continue;
            }

            // If we're on a slope, we can only go in the direction of the slope
            if let Some(Object::Slope(s)) = grid.get(&state.position) {
                if direction != &Point::from(*s) {
                    continue;
                }
            }

            // Cannot go through walls
            match grid.get(&next_position) {
                Some(Object::Wall) => continue,
                _ => (),
            }

            // Cannot visit the same point more than once
            if state.path.contains(&next_position) {
                continue;
            }

            // Otherwise, queue it up
            let new_state = State {
                position: next_position,
                path: {
                    let mut path = state.path.clone();
                    path.push(next_position);
                    path
                },
            };
            queue.push(new_state);
        }
    }

    // Find the longest path
    // Add 1 to account for leaving the grid
    let result = 1 + complete
        .iter()
        .max_by(|a, b| a.len().cmp(&b.len()))
        .unwrap()
        .len();

    println!("{result}");
    Ok(())
}
```

We can't really use [[wiki:a-star]](), since 'longest' path is actually a much harder problem than shortest path--it's [[wiki:NP-hard]](). You basically have to find all of the paths. 

So that's what we do. Keep a queue of points to examine along with the path we took to get there and explore each valid (non-overlapping + correct direction on slopes) neighboring point. 

Each time we get to the exit, record the path; at the end, record the longest and we're done. 

It's not the fastest solution, but for part 1 it's fine? 

## Part 2

> Ignore slopes. 

### Solution 1: Brute force

There it is, that makes things far longer. The only real change we need is loading the grid a bit differently:

```rust
let grid = Grid::read(input.as_str(), |c| match c {
    '#' => Some(true),
    _ => None,
});
```

And then drop the slope code and use `grid.get(&p).is_some()` to detect walls. That's really it. 

And... it's pretty slow. 

```bash
$ just run 23 2-brute

cat data/$(printf "%02d" 23).txt | cargo run --release -p day$(printf "%02d" 23) --bin part2-brute
   Compiling day23 v0.1.0 (/Users/jp/Projects/advent-of-code/2023/solutions/day23)
    Finished release [optimized] target(s) in 0.18s
     Running `target/release/part2-brute`
100000 710.137333ms
200000 1.426019042s
300000 2.131656583s
400000 2.850222125s
500000 3.651914042s
...
```

That's the number of states we've examined. We're doing hundreds of thousands a second, but it's just not long enough. 

We need to go faster!

### Solution 2: A better `Path`

So one thing that I wanted to try was to avoid all of the `clones` we're doing for `path`. What if we had a functional programming style immutable path, where 'extending' a path uses the same memory for any previous steps and only adds a new reference. So branching paths end up far more efficient. 

Let's try it!

```rust
#[derive(Debug)]
struct PathData {
    points: Vec<Point>,
    froms: Vec<Option<usize>>,
}

#[derive(Debug, Clone)]
pub struct Path {
    path: Rc<RefCell<PathData>>,
    index: usize,
    length: usize,
}

impl Path {
    pub fn new(p: Point) -> Self {
        Path {
            path: Rc::new(RefCell::new(PathData {
                points: vec![p],
                froms: vec![None],
            })),
            index: 0,
            length: 1,
        }
    }

    pub fn extend(&mut self, p: Point) -> Path {
        self.path.borrow_mut().points.push(p);
        self.path.borrow_mut().froms.push(Some(self.index));

        Path {
            path: self.path.clone(),
            index: self.path.borrow().points.len() - 1,
            length: self.length + 1,
        }
    }

    pub fn len(&self) -> usize {
        self.length
    }

    pub fn contains(&self, p: Point) -> bool {
        // Check the current point
        if self.path.borrow().points[self.index] == p {
            return true;
        }

        // Check previous points until we reach the start
        let mut index = self.index;
        while let Some(from) = self.path.borrow().froms[index] {
            if self.path.borrow().points[index] == p {
                return true;
            }
            index = from;
        }
        false
    }
}
```

What we have here is a 'hidden' shared state in `PathData`, where `Path` is the actual interface to the data. All that does is store an index into the `PathData`, which has synchronized lists of Points and indexes (for the previous node). Basically linked lists. [Entirely too many linked lists](https://rust-unofficial.github.io/too-many-lists/). 

All that changes in our solution is extending states:

```rust
// Otherwise, queue it up
let new_state = State {
    position: next_position,
    path: state.path.extend(next_position),
};
queue.push(new_state);
```

And... how's it do?

```bash
$ just run 23 2-path

cat data/$(printf "%02d" 23).txt | cargo run --release -p day$(printf "%02d" 23) --bin part2-path
   Compiling day23 v0.1.0 (/Users/jp/Projects/advent-of-code/2023/solutions/day23)
    Finished release [optimized] target(s) in 0.20s
     Running `target/release/part2-path`
100000 1.014593291s
200000 1.977192458s
300000 2.961558458s
400000 3.901192916s
500000 4.940979875s
...
```

Unfortunately... it's about 30% *slower*. 

What's happening is that we've fixed the problem with copying lots of memory by... jumping around a lot in memory. A lot more following references, especially in `contains` (I already optimized `length` to just store it in `Path`. 

So... a neat idea, but not what we needed. 

### Solution 3: Finding points of interest

If you actually look at the input (either test or real), you'll notice that the map is almost entirely corridors. There are only a handful of decision points (where you can go 3 or even 4 different directions). 

What if we replace the map with a just a list of those points and distances between them?

First, find them:

```rust
// Find 'points of interest'
log::info!("Finding splits");
let mut splits = vec![];

splits.push(Point::new(1, 0));
splits.push(Point::new(walls.bounds.max_x - 1, walls.bounds.max_y));

for y in 0..=walls.bounds.max_y {
    for x in 0..=walls.bounds.max_x {
        let p = Point::new(x, y);

        if walls.get(&p).is_some() {
            continue;
        }

        // Splits are anything with 3 or 4 non-walls
        // Or alternatively, less than 2 walls
        if DIRECTIONS
            .iter()
            .filter(|d| walls.get(&(p + **d)).is_some())
            .count()
            < 2
        {
            splits.push(p);
        }
    }
}
```

Then find the distance between each pair:

```rust
// Calculate distances between splits
log::info!("Calculating split distances");
let mut split_distances: FxHashMap<(Point, Point), usize> = FxHashMap::default();

for split in splits.iter() {
    'found: for direction in DIRECTIONS {
        let mut position = *split + direction;
        let mut distance = 1; // count the first 'direction' step
        let mut path = vec![*split, *split + direction];

        // Make sure the initial move is not out of the map or into a wall
        if !walls.bounds.contains(&position) {
            continue;
        }
        if walls.get(&position).is_some() {
            continue;
        }

        // Keep going until we find the next split in that direction
        'searching: loop {
            // If we found a split, record the distance and move on
            if splits.contains(&position) {
                split_distances.insert((*split, position), distance);
                continue 'found;
            }

            distance += 1;

            // Find the one direction (should always be one) we haven't come from
            for direction in DIRECTIONS {
                let next_position = position + direction;

                // Don't run into walls
                if walls.get(&next_position).is_some() {
                    continue;
                }

                // And don't backtrack
                if path.contains(&next_position) {
                    continue;
                }

                path.push(next_position);
                position = next_position;
                continue 'searching;
            }

            // If we didn't find a direction, this is a dead end
            break 'found;
        }
    }
}
```

And finally, do the same search as part 1, just using these nodes (and the distances between them):

```rust
// Now search for the longest path using splits
#[derive(Debug)]
struct State {
    position: Point,
    path: Vec<Point>,
    distance: usize,
}

let mut queue = Vec::new();
queue.push(State {
    position: Point::new(1, 0),
    path: Vec::new(),
    distance: 0,
});

let mut complete = Vec::new();

log::info!("Searching for longest path");
let start = std::time::Instant::now();
let mut count = 0;
while let Some(state) = queue.pop() {
    count += 1;
    if count % 1_000_000 == 0 {
        log::info!("- {:?} paths examined in {:?}", count, start.elapsed());
    }

    // Which nodes can we go to next?
    let nexts = splits.iter().filter_map(|dst| {
        if let Some(distance) = split_distances.get(&(state.position, *dst)) {
            Some((*dst, *distance))
        } else {
            None
        }
    });

    for (next, distance) in nexts {
        // If we're at the exit, we've found a complete path
        if next == Point::new(walls.bounds.max_x - 1, walls.bounds.max_y) {
            complete.push((state.path.clone(), state.distance + distance));
            continue;
        }

        // If we've already hit this split, we've found a loop
        if state.path.contains(&next) {
            continue;
        }

        // Otherwise, queue it up
        let new_state = State {
            position: next,
            path: {
                let mut path = state.path.clone();
                path.push(next);
                path
            },
            distance: state.distance + distance,
        };
        queue.push(new_state);
    }
}

let result = complete.iter().map(|(_, d)| d).max().unwrap();
```

It's a decent bit more code, but ... does it work? 

```bash
$ just time 23 2

hyperfine --warmup 3 'just run 23 2'
Benchmark 1: just run 23 2
  Time (mean ± σ):      9.702 s ±  0.093 s    [User: 9.231 s, System: 0.166 s]
  Range (min … max):    9.555 s …  9.906 s    10 runs
```

Victory (of sorts)! 

It's still 10x my worst case goal of 1 second, but at least we actually have a solution. 

And since it's the weekend, that's where I'll leave it for now, but I'm probably going to have to come back and try this one again!

## Performance

Overall (even though it's just above us), this is where we are right now:

```bash
$ just time 23 1

hyperfine --warmup 3 'just run 23 1'
Benchmark 1: just run 23 1
  Time (mean ± σ):     423.8 ms ±   8.4 ms    [User: 337.5 ms, System: 21.9 ms]
  Range (min … max):   410.7 ms … 435.2 ms    10 runs

$ just time 23 2

hyperfine --warmup 3 'just run 23 2'
Benchmark 1: just run 23 2
  Time (mean ± σ):      9.702 s ±  0.093 s    [User: 9.231 s, System: 0.166 s]
  Range (min … max):    9.555 s …  9.906 s    10 runs
```

