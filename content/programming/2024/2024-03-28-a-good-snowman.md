---
title: "A Good Snowman Is Hard To ... Solve?"
date: 2024-03-28
programming/languages:
- Rust
programming/topics:
- Algorithms
- Backtracking
- Generators
- Puzzles
- Sokoban
series:
- Rust Solvers
---
I enjoy puzzle games. I especially enjoy letting computers solve them for me :smile:. Once upon a time, I set up a [[Stateful Solvers and Iterators|framework for solving random things]](). Let's solve some more. 

Today: [A Good Snowman Is Hard To Build](https://store.steampowered.com/app/316610/A_Good_Snowman_Is_Hard_To_Build/)

It's a [[wiki:Sokoban]]() about making snowmen! You can push snowballs of three sizes around, collecting snow if you roll over it. You can push smaller snowballs onto bigger ones, stacking them. Or back off, in order to get around one another. 

And that's really it. 

There are some interesting twists (multiple snowmen, the ability to leave and re-enter levels, and even a whole second 'hard mode'), but at a basic level, it's just pushing. 

<!--more-->

## Representing the board

So, how do we represent the board? Well, the map is made of walls, empty space, and snowy spaces. Snow can become empty when you roll over it, otherwise, these don't change. Which would mean that they could be good parts of `GlobalState` (the shared state that doesn't have to be `cloned`). Meanwhile, the snowballs and player move all the time, thus being part of `LocalState`. 

But... that's not how I did it, despite the optimization. We'll just put it all in `LocalState`:

First, snowball stacks:

```rust
#[derive(Copy, Clone, PartialEq, Eq, Hash, Debug)]
enum Stack {
    Small = 1,
    Medium = 2,
    MediumSmall = 3,
    Large = 4,
    LargeSmall = 5,
    LargeMedium = 6,
    LargeMediumSmall = 7,
}

impl From<u8> for Stack {
    fn from(value: u8) -> Self {
        match value {
            1 => Stack::Small,
            2 => Stack::Medium,
            3 => Stack::MediumSmall,
            4 => Stack::Large,
            5 => Stack::LargeSmall,
            6 => Stack::LargeMedium,
            7 => Stack::LargeMediumSmall,
            _ => panic!("Invalid stack size"),
        }
    }
}
```

This could easily be a `struct Stack(bool, bool, bool)` or something like that, but this worked out well enough. And it's a nice binary representation. First bit is large, second medium, third small. 

So now, building the map:

```rust
#[derive(Copy, Clone, PartialEq, Eq, Hash, Debug)]
enum Location {
    Empty,
    Snow,
    Wall,
    Snowman(Stack),
}

#[derive(Clone, PartialEq, Eq, Hash, Debug)]
struct Map {
    width: u8,
    height: u8,
    player: Point,
    data: Vec<Location>,
}
```

## Loading the puzzles

Previously, I'd created puzzles like this by loading JSON files. It's a fair bit trickier to load, so instead, we'll just go with a text format:

```text
XXXX***XXXX
***X*1*X***
*1*******1*
***X***X***
XXXX***XXXX
XXXXX#XXXXX
```

* `X` is a wall (could be anything unwalkable)
* `*` is snow on the ground
* `-` (none in this one) is empty space
* `#` is the player
* `1` - `7` are snowballs (see `Stack` above)

We can load that easily from a string:

```rust
impl From<&str> for Map {
    fn from(value: &str) -> Self {
        use Location::*;

        let lines = value.lines().collect::<Vec<&str>>();
        let height = lines.len() as u8;
        let width = lines[0].len() as u8;

        let mut data = Vec::new();
        let mut player = Point(0, 0);

        for (y, line) in lines.iter().enumerate() {
            for (x, c) in line.chars().enumerate() {
                match c {
                    '-' => data.push(Empty),
                    '*' => data.push(Snow),
                    'X' => data.push(Wall),
                    '#' => {
                        data.push(Empty);
                        player = Point(x as i8, y as i8);
                    }
                    _ => {
                        let value = c.to_digit(10).unwrap() as u8;
                        data.push(Snowman(value.into()));
                    }
                }
            }
        }

        Map {
            width,
            height,
            player,
            data,
        }
    }
}
```

## Checking for solvedness

Okay, we have the basic data structure in place, so now we need the solver functions: `is_valid`, `is_solved`, `next_states`, and `heuristic`. 

Let's start with `is_solved`, that's easy:

```rust
impl<G> State<G, Step> for Map {
    fn is_solved(&self, _: &G) -> bool {
        use Location::*;
        use Stack::*;

        // All snowmen are completely formed
        for y in 0..self.height {
            for x in 0..self.width {
                match self.get(Point(x as i8, y as i8)) {
                    Some(Snowman(LargeMediumSmall)) => continue,
                    Some(Snowman(_)) => return false,
                    _ => continue,
                }
            }
        }

        return true;
    }
}
```

Yup, that's it. 

## Checking for invalid states

Okay, next let's validate!

This is an implementation choice. If you never generate an invalid state, this function can just `return true`. But conversely, you can use this to check for technically 'valid' states that you could move into, but that can *never* lead to a solved state, which is what I did here:

```rust
impl<G> State<G, Step> for Map {
    fn is_valid(&self, g: &G) -> bool {
        use Location::*;
        use Stack::*;

        // If we're solved, we're valid
        if self.is_solved(g) {
            return true;
        }

        // Check that we have or can build the proper number of snowmen
        let mut small_balls = 0;
        let mut medium_balls = 0;
        let mut large_balls = 0;
        let mut snow_count = 0;

        for y in 0..self.height {
            for x in 0..self.width {
                match self.get(Point(x as i8, y as i8)) {
                    Some(Snowman(any)) => {
                        small_balls += if (any as u8) & 1 != 0 { 1 } else { 0 };
                        medium_balls += if (any as u8) & 2 != 0 { 1 } else { 0 };
                        large_balls += if (any as u8) & 4 != 0 { 1 } else { 0 };
                    }
                    Some(Snow) => snow_count += 1,
                    _ => continue,
                }
            }
        }

        if small_balls < large_balls {
            return false;
        }
        if small_balls + medium_balls < large_balls {
            return false;
        }

        // We have to have enough snow left to transform so that we have N L/M/S
        let target_snowmen = (small_balls + medium_balls + large_balls) / 3;

        // Not enough remaining heads
        if small_balls < target_snowmen {
            return false;
        }

        // Not enough heads to match bellies (even if we used all remaining snow)
        if medium_balls + small_balls.min(snow_count) < target_snowmen {
            return false;
        }

        // Not enough butts, even if we use bellies and heads with remaining snow
        // This is imperfect, but should help
        if large_balls + medium_balls.min(snow_count) + small_balls.min(snow_count) < target_snowmen
        {
            return false;
        }

        // We have too many bottoms; can't downgrade them
        if large_balls > target_snowmen {
            return false;
        }

        // This overestimates
        // Technically a snowman is 'moveable' if you can either stack them
        // Or the target snowman is itself moveable
        // Which we can calculate, but I haven't yet
        let is_moveable = |l: Location| match l {
            Empty => true,
            Snow => true,
            Snowman(_) => true,
            _ => false,
        };

        // Any non-large in a corner is trapped (and thus invalid)
        // Larges in a non-target corner are also bad
        for y in 0..self.height {
            for x in 0..self.width {
                let (is_snowman, is_large) = match self.get(Point(x as i8, y as i8)) {
                    Some(Snowman(LargeMediumSmall | LargeMedium | Large)) => (true, true),
                    Some(Snowman(_)) => (true, false),
                    _ => (false, false),
                };
                if !is_snowman {
                    continue;
                }

                let north = self.get(Point(x as i8, y as i8 - 1)).unwrap_or(Wall);
                let south = self.get(Point(x as i8, y as i8 + 1)).unwrap_or(Wall);
                let east = self.get(Point(x as i8 + 1, y as i8)).unwrap_or(Wall);
                let west = self.get(Point(x as i8 - 1, y as i8)).unwrap_or(Wall);

                if !is_moveable(north) && !is_moveable(west) {
                    return false;
                }
                if !is_moveable(north) && !is_moveable(east) {
                    return false;
                }
                if !is_moveable(south) && !is_moveable(west) {
                    return false;
                }
                if !is_moveable(south) && !is_moveable(east) {
                    return false;
                }
            }
        }

        // Otherwise, assume valid
        return true;
    }
}
```

There are a few cases here that I added as I kept solving more levels and I think they should all be commented fairly well. For example, if you start with 6 snowballs (in various states), then you know that you will need to build 2 snowmen. So you will need 2 small balls / heads. And you can never make a snowball smaller, so if you ever end up with less than 2... we'll `!is_valid`. 

Likewise, if you get small balls stuck in corners. You can't push them out and you can't put a larger ball on a smaller one. `!is_valid`. 

This one, I really do need to work on. It's not perfect right now, as this state is technically invalid, but I can't catch it:

```text
XXXX
X-1-
X1--
X---
```

Because if you would push either ball into the corner, it's invalidated. Now, that branch of the solver will be pruned as soon as either is pushed there, but because each step of the player is a separate 'state', it's still not efficient. But that's a problem for another day. 

## Generating next states

Okay, here's the meat of the problem. How do we take a state and generate the `next_states` from it? 

Well, like this:

```rust
impl<G> State<G, Step> for Map {
    fn next_states(&self, _: &G) -> Option<Vec<(i64, Step, Map)>> {
        use Location::*;
        use Stack::*;
        use Step::*;

        let mut states = Vec::new();

        let moves = [
            (North, Point(0, -1)),
            (South, Point(0, 1)),
            (East, Point(1, 0)),
            (West, Point(-1, 0)),
        ];

        for (step, delta) in moves.into_iter() {
            let next = self.player + delta;
            let next_2 = next + delta;

            let target = self.get(next);
            let target_2 = self.get(next_2);

            // Can't move out of bounds
            if target.is_none() {
                continue;
            }

            // Can't move into a wall
            if let Wall = target.unwrap() {
                continue;
            }

            // The target is empty, just move into it
            if let Empty = target.unwrap() {
                let mut new_state = self.clone();
                new_state.player = next;
                states.push((MOVE_EMPTY_COST, step, new_state));
                continue;
            }

            // Likewise onto snow
            if let Snow = target.unwrap() {
                let mut new_state = self.clone();
                new_state.player = next;
                states.push((MOVE_SNOW_COST, step, new_state));
                continue;
            }

            // Try to push a snowman together or apart
            if let Snowman(any) = target.unwrap() {
                // Single balls can be pushed into empty spaces, snow (growing), and valid snowmen
                if target_2.is_some() && (any == Small || any == Medium || any == Large) {
                    // Empty spaces always work
                    if let Empty = target_2.unwrap() {
                        let mut new_state = self.clone();
                        new_state.player = next;
                        new_state.set(next, Empty);
                        new_state.set(next_2, Snowman(any));
                        states.push((PUSH_EMPTY_COST, step, new_state));
                        continue;
                    }

                    // Snow works and grows the ball
                    // Large stays large
                    // Snow is always removed (even if large -> large)
                    if let Snow = target_2.unwrap() {
                        let new_size = match any {
                            Small => Medium,
                            Medium => Large,
                            Large => Large,
                            _ => continue,
                        };

                        let mut new_state = self.clone();
                        new_state.player = next;
                        new_state.set(next, Empty);
                        new_state.set(next_2, Snowman(new_size));
                        states.push((PUSH_SNOW_COST, step, new_state));
                        continue;
                    }

                    // Single balls can be pushed onto other smaller balls
                    if let Snowman(other) = target_2.unwrap() {
                        let combined = match (any, other) {
                            (Small, Medium) => Some(MediumSmall),
                            (Small, Large) => Some(LargeSmall),
                            (Medium, Large) => Some(LargeMedium),
                            (Small, LargeMedium) => Some(LargeMediumSmall),
                            _ => None,
                        };

                        if let Some(combined) = combined {
                            let mut new_state = self.clone();
                            new_state.player = next;
                            new_state.set(next, Empty);
                            new_state.set(next_2, Snowman(combined));
                            states.push((STACK_COST, step, new_state));
                            continue;
                        }
                    }
                }

                // Stacks can be broken apart if the target is empty
                // Note: In these cases, the player *does not move*
                if target_2.is_some()
                    && (any == MediumSmall || any == LargeSmall || any == LargeMedium)
                {
                    // Pushing into empty space
                    if let Empty = target_2.unwrap() {
                        let (a, b) = match any {
                            MediumSmall => (Medium, Small),
                            LargeSmall => (Large, Small),
                            LargeMedium => (Large, Medium),
                            _ => panic!("Invalid stack size"),
                        };

                        let mut new_state = self.clone();
                        new_state.set(next, Snowman(a));
                        new_state.set(next_2, Snowman(b));
                        states.push((UNSTACK_EMPTY_COST, step, new_state));
                        continue;
                    }

                    // Pushing onto snow
                    if let Snow = target_2.unwrap() {
                        let (a, b) = match any {
                            MediumSmall => (Medium, Medium),
                            LargeSmall => (Large, Medium),
                            LargeMedium => (Large, Large),
                            _ => panic!("Invalid stack size"),
                        };

                        let mut new_state = self.clone();
                        new_state.set(next, Snowman(a));
                        new_state.set(next_2, Snowman(b));
                        states.push((UNSTACK_SNOW_COST, step, new_state));
                        continue;
                    }
                }
            }

            // If we made it this far, the state is invalid for some other reason
            // println!("Invalid state: {:?}", self);
            // println!("Moving: {:?}", delta);
        }

        // If we have states, return them
        if !states.is_empty() {
            Some(states)
        } else {
            None
        }
    }
}
```

Okay, first the signature. If you don't recall from previous posts (actually, you won't, I changed it :smile:), the `next_states` function should return a `Vec` of possible states from the one we're in. For each, it should return a tuple of `(i64, StepType, LocalStateType)` where `StepType` represents taking one step (to rebuild the path) and `LocalStateType` is the state that changes with each step through the puzzle. In this case, `StepType` is a `Step`, `North`, `South`, `East`, `West` and `LocalStateType` is the `Map` above (a grid of `Location` and `Stack`). 

From there, we have always exactly 4 moves:

```rust
let moves = [
    (North, Point(0, -1)),
    (South, Point(0, 1)),
    (East, Point(1, 0)),
    (West, Point(-1, 0)),
];
```

For each of those, we'll do a few things in sequence (matching the code above):

* Generate what point we'd move on to (`next`) and the spot after that (`next_2`); the latter is used if we push a snowball onto (or off of) an existing snowman
* If either of those is out of bounds `None` or solid `Some(Wall)`, we can't move, so do nothing. 
* If the `next` space is `Empty` (or `Snow`), we just walk onto it, ignore `next_2`
* If `next` is a `Snowman`, then `next_2` has to be `Empty` or `Snow`, otherwise, ignore this state; otherwise:
  * If it's a single small/medium ball and `next_2` is medium/large, we can stack them
  * If it's incomplete snowman and `next_2` is `Empty` or `Snow`, we can push it off

Turn all of that to code... and we have our next states!

This was a lot of trial and error and... I really should have written more tests. But it was fun to write!

## Trying the solver

Don't worry, we'll come back to the heuristics. :smile:

For now though, that's all we need to write the solver:

```rust
fn main() {
    env_logger::init();

    let input = io::read_to_string(io::stdin()).unwrap();
    let initial_state = Map::from(input.as_str());

    println!("initial: {}", initial_state);

    let mut solver = Solver::new((), initial_state.clone());

    while let Some(state) = solver.next() {
        if solver.states_checked() % 100000 != 0 {
            continue;
        }

        println!("===== ===== ===== ===== =====");
        println!("state: {}", state);
        println!(
            "{} states checked, {} in queue, {} invalidated, {} seconds, heuristic: {}",
            solver.states_checked(),
            solver.in_queue(),
            solver.states_invalidated(),
            solver.time_spent(),
            state.heuristic(&()),
        );
    }

    let solution = solver.get_solution();
    if solution.is_none() {
        println!("no solution found");
        return;
    }
    let solution = solution.unwrap();

    println!("solution: {}", solution);

    let mut steps = String::new();
    for step in solver.path(&initial_state, &solution).unwrap() {
        match step {
            Step::North => steps += "W",
            Step::South => steps += "S",
            Step::East => steps += "D",
            Step::West => steps += "A",
        }
    }
    println!("path: {}", steps);

    println!(
        "{} states, {} seconds",
        solver.states_checked(),
        solver.time_spent()
    );
}
```

Load it up, have a lot of debugging in there and... that's it. For a lot of the simpler puzzles, it just works:

```bash
$ cat data/good-snowman/Mary.txt | ./target/release/good-snowman

initial: map:
  *****
  *4X3*
  *****
  X#XXX

solution: map:
  *#7-*
  *-X-*
  *****
  X-XXX

path: WWAWDDAASSDDDDWWADSSAWDWWAADSSAWDWASSAAAWWD
116 states, 0.00035992003 seconds
```

Some of them take a fair bit longer than that. And the solutions are *not* optimal at the moment, which really feels like a bug, shouldn't it be doing a breadth first search? 

But, for the purposes of running through these puzzles, it works pretty well!

## Back to heuristics

Okay, so back a step to those heuristics I was talking about. 

We're running basically [[wiki:A star]]() to solve these problems, over the puzzle state space. In this case, we're always returning `1` for the step cost, because each move is the same number of key presses in the final solution. If we wanted to push snowmen as little as possible, we could change this. 

But failing that, a heuristic should help order which states we look at in which order. 

So here we go:

```rust
impl<G> State<G, Step> for Map {
    fn heuristic(&self, _global: &G) -> i64 {
        use Location::*;
        use Stack::*;

        let mut score = 0;

        // // Add the sum of distances between each pair of incomplete snowmen
        // for y in 0..self.height {
        //     for x in 0..self.width {
        //         match self.get(Point(x as i8, y as i8)) {
        //             Some(Snowman(LargeMediumSmall)) => continue,
        //             Some(Snowman(_)) => {
        //                 for y2 in 0..self.height {
        //                     for x2 in 0..self.width {
        //                         match self.get(Point(x2 as i8, y2 as i8)) {
        //                             Some(Snowman(LargeMediumSmall)) => continue,
        //                             Some(Snowman(_)) => {
        //                                 let dx = x as i64 - x2 as i64;
        //                                 let dy = y as i64 - y2 as i64;
        //                                 score += dx.abs() + dy.abs();
        //                             },
        //                             _ => continue,
        //                         }
        //                     }
        //                 }
        //             },
        //             _ => continue,
        //         }
        //     }
        // }

        // Add the distance from the player to the nearest incomplete snowman
        let mut distance = (self.width as i8 + self.height as i8) as i64;
        for y in 0..self.height {
            for x in 0..self.width {
                match self.get(Point(x as i8, y as i8)) {
                    Some(Snowman(LargeMediumSmall)) => continue,
                    Some(Snowman(_)) => {
                        let dx = (self.player.0 - (x as i8)).abs() as i64;
                        let dy = (self.player.1 - (y as i8)).abs() as i64;
                        distance = distance.min(dx + dy);
                    }
                    _ => continue,
                }
            }
        }
        score += distance;

        // Add the distance from each small/medium to the nearest available medium/large
        for y in 0..self.height {
            for x in 0..self.width {
                match self.get(Point(x as i8, y as i8)) {
                    Some(Snowman(Small)) => {
                        let mut distance = (self.width as i8 + self.height as i8) as i64;
                        for y2 in 0..self.height {
                            for x2 in 0..self.width {
                                match self.get(Point(x2 as i8, y2 as i8)) {
                                    Some(Snowman(Medium)) | Some(Snowman(LargeMedium)) => {
                                        let dx = (x as i8 - x2 as i8).abs() as i64;
                                        let dy = (y as i8 - y2 as i8).abs() as i64;
                                        distance = distance.min(dx + dy);
                                    }
                                    _ => continue,
                                }
                            }
                        }
                        score += distance;
                    }
                    Some(Snowman(Medium)) => {
                        let mut distance = (self.width as i8 + self.height as i8) as i64;
                        for y2 in 0..self.height {
                            for x2 in 0..self.width {
                                match self.get(Point(x2 as i8, y2 as i8)) {
                                    Some(Snowman(Large)) => {
                                        let dx = (x as i8 - x2 as i8).abs() as i64;
                                        let dy = (y as i8 - y2 as i8).abs() as i64;
                                        distance = distance.min(dx + dy);
                                    }
                                    _ => continue,
                                }
                            }
                        }
                        score += distance;
                    }
                    _ => continue,
                }
            }
        }

        // // Add various points per incomplete snowman
        // for y in 0..self.height {
        //     for x in 0..self.width {
        //         match self.get(Point(x as i8, y as i8)) {
        //             Some(Snowman(LargeMediumSmall)) => continue,
        //             Some(Snowman(any)) => score += 10 * (any as i64),
        //             _ => continue,
        //         }
        //     }
        // }

        // // Add points for snow
        // for y in 0..self.height {
        //     for x in 0..self.width {
        //         match self.get(Point(x as i8, y as i8)) {
        //             Some(Snow) => score += 1,
        //             _ => continue,
        //         }
        //     }
        // }

        return score;
    }
}
```

As you can see, it's not perfect. In `A Star`, you are guaranteed a solution, but if your heuristic is less than the actual number of steps, you're not guaranteed an optimal solution. So I mostly messed with a bunch of different values to see what we could actually get. And this does help the solver significantly, although we could do better. 

At this point though, this is more than enough to solve the basic game. All 30 puzzles. A few didn't solve quickly (at all), but they all do eventually finish. So... what's next? 

## Extra credit: Targetted solutions

Well, it turns out there's a second 'hard mode', where you dream about where you build the snowmen and then take those locations and build metasnowmen? It gets weird. Anyways, to solve this, we want to be able to set a specific location for the snowman to be built at. 

This actually isn't that much of a change. 

First, in `Map`, add `targets: Option<Vec<Point>>`. If `None`, do what we did before. Otherwise, `is_solved` will take this into account. I'm using `+` for a target on `Empty` and `=` for a target on `Snow` (so we don't lose out on that snow). 

Next, in `is_solved`:

```rust
// If there are targets, any completed snowman not on a target is invalid
// TODO: This probably shouldn't be in both is_valid and is_solved
if let Some(targets) = &self.targets {
    for y in 0..self.height {
        for x in 0..self.width {
            if let Some(Snowman(LargeMediumSmall)) = self.get(Point(x as i8, y as i8)) {
                if !targets.contains(&Point(x as i8, y as i8)) {
                    return false;
                }
            }
        }
    }
}
```

And that's really it. I did also invalidate (as mentioned) states that had a snowman complete in the wrong place, since we can't break them up once formed, but that's really it. 

## Future work

So, it works and I 100% completed the game. What could possibly be next? 

Well, the performance is still bothering me a bit. So one solution would be, rather than generating each step of the player as a state, instead generate all possible state changes--those being pushing/stacking/unstacking a snowball. That will branch much faster but also generate far fewer states (and let caching work better). Worth a try!

But that's a post for another day. Onward!