---
title: "AoC 2022 Day 24: Blizzinator"
date: 2022-12-24 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
## Source: [Blizzard Basin](https://adventofcode.com/2022/day/24)

## Part 1

> Given a map with a series of moving walls (that wrap when the hit the edges of the simulation), calculate the fastest route from the top left to the bottom right. 

<!--more-->

<video controls src="/embeds/2022/aoc24-1.mp4"></video>

Yeah... that's a lot of snow. 

So basically, as is often the case, there are two parts to this problem:

1. Get the simulation working (so that we know where the walls are when)
2. Writing an algorithm that finds the best path through that simulation

For #1: 

```rust
struct Map {
    width: usize,
    height: usize,
    blizzards: Vec<(Point, Point)>,
    occupied: Rc<RefCell<HashMap<(usize, usize, usize), bool>>>,
}

impl From<&Path> for Map {
    fn from(filename: &Path) -> Self {
        let lines = read_lines(filename);

        let width = lines[0].len();
        let height = lines.len();

        let mut blizzards = Vec::new();

        for (y, line) in lines.into_iter().enumerate() {
            for (x, c) in line.chars().enumerate() {
                let p = Point::new(x as isize, y as isize);
                match c {
                    '.' | '#' => {},
                    '^' => blizzards.push((p, Point::new(0, -1))),
                    'v' => blizzards.push((p, Point::new(0, 1))),
                    '<' => blizzards.push((p, Point::new(-1, 0))),
                    '>' => blizzards.push((p, Point::new(1, 0))),
                    _ => panic!("unknown map character {c}")
                }
            }
        }

        Map { width, height, blizzards, occupied: Rc::new(RefCell::new(HashMap::new())) }
    }
}

impl Map {
    fn occupied(&self, x: usize, y: usize, t: usize) -> bool {
        // Constant walls
        if x == 0 || x == self.width - 1{
            return true;
        }
        if y == 0 {
            return x != 1;
        }
        if y == self.height - 1 {
            return x != self.width - 2;
        }

        // Check cache
        if let Some(result) = self.occupied.borrow().get(&(x, y, t)) {
            return *result;
        }

        // Calculate blizzard positions, find if any is at that point and time
        // Top left is offset by 1 (at beginning and end) to account for top/left
        // Modulus is offset by 2 to account for both walls in each direction
        let mut is_occupied = false;
        
        let x_loop_fix = ((self.width - 2) * (1 + t / (self.width - 2))) as isize;
        let y_loop_fix = ((self.height - 2) * (1 + t / (self.height - 2))) as isize;

        for (origin, delta) in self.blizzards.iter() {
            if x == 1 + (x_loop_fix + origin.x - 1 + delta.x * t as isize) as usize % (self.width - 2)
            && y == 1 + (y_loop_fix + origin.y - 1 + delta.y * t as isize) as usize % (self.height - 2) {
                is_occupied = true;
                break;
            }
        }

        // Update cache and return
        self.occupied.borrow_mut().insert((x, y, t), is_occupied);
        is_occupied
    }
}
```

I'm doing a bit of caching here, but other than that, what we essentially have is a 3-dimensional map. `t` could be time, but it could just as easily be a `z` dimension and we're trying to climb through this cube. 

For #2, I'm actually (just when we're almost done) going to {{<wikipedia text="A*" title="A* search algorithm">}} it up in here:

```rust
fn part1(filename: &Path) -> String {
    let map = Map::from(filename);

    type Point3u = (usize, usize, usize);

    let mut open = PriorityQueue::new();
    let mut closed = HashSet::new();
    let mut previous: HashMap<Point3u, Point3u> = HashMap::new();
    let mut final_time = 0;

    open.push((1 as usize, 0 as usize, 0 as usize), 0 as isize);

    loop {
        let ((x, y, t), _) = open.pop().unwrap();
        closed.insert((x, y, t));

        // Solved
        if x == map.width - 2 && y == map.height - 1 {
            final_time = t;
            break;
        }

        for (xd, yd) in [(0 as isize, -1 as isize), (0, 1), (-1, 0), (1, 0), (0, 0)] {
            // Skip out of bounds cases
            if y == 0 && yd == -1 || (x == map.width - 2 && y == map.height - 1 && yd == 1) {
                continue;
            }

            let xp = (x as isize + xd) as usize;
            let yp = (y as isize + yd) as usize;
            let tp = t + 1;

            if closed.contains(&(xp, yp, tp)) {
                continue;
            }

            if map.occupied(xp, yp, tp) {
                continue;
            }

            if !previous.contains_key(&(xp, yp, tp)) || t < previous.get(&(xp, yp, tp)).unwrap().2 {
                previous.insert((xp, yp, tp), (x, y, t));
            } 

            let d_remaining = map.width - xp - 2 + map.height - yp - 1;
            let t_guess = (tp as isize + d_remaining as isize) * -1;
            open.push((xp, yp, tp), t_guess);
        }
    }

    final_time.to_string()
}
```

That really is the A* algorithm in a nutshell:

* Keep a list of `open` nodes with priorities (in this case, the distance we've traveled + the expected distance to get to the exit; as long as the expected distance estimate is less than or equal to reality, this will be an optimal path)
* Keep a list of `closed` nodes we've already visited
* While we're not done:
  * Take the next `open` node, `close` it, and then for each neighbor:
    * Calculate the new distance + estimate, insert it into `open`

The estimate function is just the {{<wikipedia "Manhattan distance">}} directly to the exit, since that's the best we could do. 

And... that's it for part 1. Not actually that bad. 

Well. For me. For the poor elf out in all that snow? Pretty bad. 

## Part 2

> After reaching the exit, return to the entrance, then go back to the exit again. 

This is more interesting than it could be, since the walls move around. But if you still image it as a three dimensional cube, it just got much taller, but you still have to go from one corner of one level to the next, then back and forth one more time. 

Not my best code, but I think it works well enough:

```rust
fn part2(filename: &Path) -> String {
    let map = Map::from(filename);

    type Point4u = (usize, usize, usize, usize);

    let mut open = PriorityQueue::new();
    let mut closed = HashSet::new();
    let mut previous: HashMap<Point4u, Point4u> = HashMap::new();
    let mut final_time = 0;

    open.push((1 as usize, 0 as usize, 0 as usize, 0 as usize), 0 as isize);

    loop {
        let ((x, y, t, phase), _) = open.pop().unwrap();
        closed.insert((x, y, t));

        // Solved when we reach phase 3 and are at the exit
        // Phase 0 -> exit, 1 -> entrance, 2 -> exit, 3 is at exit 
        if phase == 3 && x == map.width - 2 && y == map.height - 1 {
            final_time = t;
            break;
        }

        for (xd, yd) in [(0 as isize, -1 as isize), (0, 1), (-1, 0), (1, 0), (0, 0)] {
            // Skip out of bounds cases
            if y == 0 && yd == -1 || (x == map.width - 2 && y == map.height - 1 && yd == 1) {
                continue;
            }

            let xp = (x as isize + xd) as usize;
            let yp = (y as isize + yd) as usize;
            let tp = t + 1;

            if closed.contains(&(xp, yp, tp)) {
                continue;
            }

            if map.occupied(xp, yp, tp) {
                continue;
            }

            let mut d_remaining = 0;

            // Distance to next phase
            // On even phases, go to the exit; on odd, the entrance
            if phase % 2 == 0 {
                d_remaining += map.width - xp - 2 + map.height - yp - 1
            } else {
                d_remaining += xp - 1 + yp;
            };

            // Next phase if d is 0
            let pp = if d_remaining == 0 { phase + 1 } else { phase };

            if !previous.contains_key(&(xp, yp, tp, pp)) || t < previous.get(&(xp, yp, tp, pp)).unwrap().2 {
                previous.insert((xp, yp, tp, pp), (x, y, t, phase));
            } 

            // Distance for unreached phases
            d_remaining += (2 - phase) * (map.width - 2 + map.height - 1);

            // Guessed best time for a*
            let t_guess = (tp as isize + d_remaining as isize) * -1;
            open.push((xp, yp, tp, pp), t_guess);
        }
    }

    final_time.to_string()
}
```

The only real difference is that I'm adding a 4th dimension: `phase`. This is `0` when going from entrance to exit, `1` when going back, `2` when going back to the exit once again, and `3` the last frame when leaving the simulation. 

We do have to account for those extra trips in the distance estimations, but other than that, that's really it. 

I didn't actually render the full A* search and I really should, but so it goes. 

## Performance

```bash
$ ./target/release/24-blizzinator 1 data/24.txt

238
took 216.284708ms

$ ./target/release/24-blizzinator 2 data/24.txt

751
took 2.888319708s
```

A bit more than 3x to go 3x the distance, but since the map moves around so much that you might have to take a different branch, that's to be expected. 

Only one day left! Onward!