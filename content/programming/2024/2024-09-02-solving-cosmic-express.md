---
title: "Solving Cosmic Express"
date: 2024-09-02
programming/languages:
- Rust
programming/topics:
- Algorithms
- Backtracking
- Generators
- Puzzles
- Pathfinding
aliases:
- /2024/09/02/solving-cosmic-encounter/
series:
- Rust Solvers
---
Another [[Rust Solvers]]() puzzle: [Cosmic Express](https://store.steampowered.com/app/583270/Cosmic_Express/). Basically, it's a routefinding puzzle. You have a train that needs a track from entrance to exit, picking up and dropping off cargo on the way. 

It's actual a relatively simple puzzle, so far as things go, but one thing that's interesting from a solving perspective is that branching paths *really* don't work great with my solver code. Paths just have a crazy branching factor when compared to (for example) [playing one of a handful of cards]({{<ref "2024-06-17-the-golf-peaks-of-solving">}}). 

But it's still an interesting puzzle! 

<!--more-->

- - - 

{{<toc>}}

## Representing the simulation

Okay, first as always, what structs do we have to represent the puzzle in our solver? For the global state, we have:

```rust
#[derive(Clone, Debug, Serialize, Deserialize)]
struct CosmicExpressGlobal {
    width: isize,
    height: isize,
    length: isize,

    entrance: Point,
    exit: Point,
    walls: Vec<Point>,
}
```

This is a standard grid with a few non-changing elements, such as the `entrance` and `exit` into the level and the non-passable `walls` that you can't path through. One interesting aspect here is that the aliens/houses (the cargo you pick up and where you drop it off) are also treated as `walls`, so I just also include them in this map. 

Also, I could definitely use a `HashSet` for `walls`, it would fit, but this is one of those interesting cases where that's actually slower than just searching through a `Vec` (I benchmarked it). There are just so few walls (<10) on most levels, it's not worth the cost to calculate the hash of `Point` over and over again. 

Next up, the local state:

```rust
#[derive(Copy, Clone, Debug, PartialEq, Eq, Serialize, Deserialize, Hash, Ord, PartialOrd)]
enum Color {
    Purple,
    Orange,
    Green,
}

#[derive(Clone, PartialEq, Eq, Debug)]
struct CosmicExpressLocal {
    // The path the train has taken so far
    path: Vec<Point>,

    // The current seats of the train
    // Seats contains the color of the alien in the seat
    // Goop is a flag on if a seat has been 'gooped' by a green alien
    seats: Vec<Option<Color>>,
    seat_goop: Vec<bool>,

    // Remaining aliens that haven't been picked up / houses that haven't been delivered to
    aliens: Vec<(Point, Color)>,
    houses: Vec<(Point, Color)>,
}
```

In this case, we have an ordered list of all the points visited on this `path` first. Next up, we have `seats`. The train has nultiple seats that follow along the engine, which are basically at `1..=seats.len()` in `path`. 

What `seats` actually holds is an `Option<Color>` representing which color alien is in the seat (`Some`) or if it's empty `None`. Then `seat_goop` is another array representing if a `Green` alien has sat in the seat at any point--no non-green alien will sit in a seat after a green has. Both of these `Vec` are always exactly the same length as the number of seats on the train. 

I could have implemented this as `seats: Vec<(bool, Option<Color>)>`, but honestly, I added the `seat_goop` once the seat color was already implemented, so this seemed find. 

Finally, `aliens` and `houses` represent remaining `aliens` to pick up (this `Vec` will shrink over time) and `houses` to take them to, if the colors matches. 

## Solving Cosmic Express

Okay, so what's the basic model for solving this? 

```rust
impl State<CosmicExpressGlobal, ()> for CosmicExpressLocal {
    fn is_valid(&self, g: &CosmicExpressGlobal) -> bool {
        // Check goop, if we have no un-gooped seats and there are non-Green aliens left, it's invalid
        if self.seat_goop.iter().all(|&b| b)
            && self
                .aliens
                .iter()
                .filter(|(_, c)| *c != Color::Green)
                .count()
                > 0
        {
            return false;
        }

        // All validators passed
        true
    }

    fn is_solved(&self, g: &CosmicExpressGlobal) -> bool {
        self.aliens.len() == 0 
            && self.houses.len() == 0
            && self.path.last().unwrap() == &g.exit
    }

    fn next_states(&self, g: &CosmicExpressGlobal) -> Option<Vec<(i64, (), Self)>> {
        let mut result = Vec::with_capacity(4);

        'neighbor: for p in self.path.last().unwrap().neighbors() {
            // Validate that the next point is valid
            // Cannot leave the bounds unless on entrance or exit
            if !(g.entrance == p || g.exit == p)
                && (p.x < 1 || p.y < 1 || p.x > g.width || p.y > g.height)
            {
                continue 'neighbor;
            }

            // Cannot move onto walls
            if g.walls.contains(&p) {
                continue 'neighbor;
            }

            // Cannot visit the same tile more than once
            for p2 in self.path.iter() {
                if &p == p2 {
                    continue 'neighbor;
                }
            }

            // Assume we can move, create the new state
            let mut new_local = self.clone();
            new_local.path.push(p);

            // Update each seat
            for (seat_index, seat_point) in self.path.iter().rev().skip(1).enumerate() {
                // If we're over the end of the seats, we're done
                if seat_index >= new_local.seats.len() {
                    break;
                }

                let mut seat_contents = new_local.seats[seat_index];

                // Full seats next to the correct house; drop it off
                if let Some(seat_color) = seat_contents {
                    for (house_index, (house_point, house_color)) in
                        new_local.houses.iter().enumerate()
                    {
                        if seat_point.manhattan_distance(*house_point) == 1
                            && seat_color == *house_color
                        {
                            new_local.houses.remove(house_index);
                            new_local.seats[seat_index] = None;
                            seat_contents = None;
                            break;
                        }
                    }
                }

                // Empty seats next to an alien; pick it up
                if seat_contents.is_none() {
                    // Find all viable aliens
                    // This has to be done this way because if two try to load at once, none get to
                    let mut viable_aliens = Vec::new();
                    for (alien_index, (alien_point, alien_color)) in
                        new_local.aliens.iter().enumerate()
                    {
                        if seat_point.manhattan_distance(*alien_point) == 1 {
                            // Non-green aliens will not try to sit in gooped seats
                            if alien_color != &Color::Green && new_local.seat_goop[seat_index] {
                                continue;
                            }

                            // Record that this alien can be loaded
                            viable_aliens.push((alien_index, *alien_color));
                        }
                    }

                    // If we found exactly one, load it
                    if viable_aliens.len() == 1 {
                        let (alien_index, alien_color) = viable_aliens[0];

                        new_local.aliens.remove(alien_index);
                        new_local.seats[seat_index] = Some(alien_color);

                        if alien_color == Color::Green {
                            new_local.seat_goop[seat_index] = true;
                        }
                    }
                }
            }

            result.push((1, (), new_local));
        }

        // We'll always have nodes, so always return
        // We're relying on is_valid to filter impossible states this time
        Some(result)
    }

    fn heuristic(&self, global: &CosmicExpressGlobal) -> i64 {
        let mut heuristic = 0;

        // Very basic heuristic; just how many entities are left
        if *HEURISTIC_COUNT_ENTITIES {
            heuristic += ((self.aliens.len() + self.houses.len()) as isize
                * global.width.max(global.height)) as i64;
        }

        // Custom heuristic to hug walls (hopefully cuts down on path segments)
        if *HEURISTIC_HUG_WALLS {
            if self
                .path
                .last()
                .unwrap()
                .neighbors()
                .iter()
                .filter(|n| 
                    global.walls.contains(n) 
                    || self.path.contains(n)
                    || n.x <= 1
                    || n.y <= 1
                    || n.x >= global.width
                    || n.y >= global.height
                )
                .count()
                <= 1
            {
                heuristic += 1000;
            }
        }

        // Custom heuristic to actually guess the possible path
        if *HEURISTIC_NEAREST_HOUSE {
            // ... explained later ...
        }

        heuristic
    }
}
```

`is_valid` doesn't actually do much, although it does bail out if we've picked up too many green aliens to solve the puzzle. But for most of my runs, I did use a [much better validator](#floodfill-validator), which I'll talk about later. 

Likewise, the `is_solved` is just: all aliens and houses are cleared + at the exit. 

The `heuristic` also has a slightly more complicated section [later](#a-simple-heuristic)

`next_states`, as always, contains the simulation itself, so is a bit more complicated. 

Basically:

* Find the end of current path; for each neighbor:
  * If it tries to exit the level, skip
  * If it tries to walk into a wall (including aliens and houses), skip
  * Paths cannot cross (yet)
  * Otherwise:
    * Update each seat
      * If an empty seat is next to a alien, pick it up (complication: not if there are two to pick up at once)
        * Green aliens goop their seats
      * If an alien is in a seat next to a matching (empty) house, drop it off

That's... actually it. It's interesting how relatively simple generating states can be. It does branch rather much though...

But for basic levels, that's enough to solve the problem!

## Loading level data

This is actually my second time through solving this puzzle. For the first time around, I had a slightly more complicated model with multiple `entrances` / `exits` and `entities` for `Wall`/`Alien`/`House`:

```rust
// Used only for loading
#[derive(Copy, Clone, Debug, Serialize, Deserialize)]
enum Entity {
    Wall,
    Alien { color: Color },
    House { color: Color },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct CosmicExpressDefinition {
    width: isize,
    height: isize,
    length: isize,

    entrances: Vec<Point>,
    exits: Vec<Point>,

    entities: Vec<(Point, Entity)>,
}
```

One thing that's interesting here though (and you might already see it with the `#[derive(Serialize, Deserialize)]`): I can write out the levels as JSON and use [serde](https://serde.rs/) + [serde_json](https://github.com/serde-rs/json) to automagically parse them!

So something like this:

```json
{
  "width": 7,
  "height": 7,
  "length": 2,

  "entrances": [{ "x": 0, "y": 4 }],
  "exits": [{ "x": 8, "y": 4 }],
  "entities": [
    [{ "x": 4, "y": 1 }, "Wall"],
    [{ "x": 4, "y": 7 }, "Wall"],
    [{ "x": 6, "y": 4 }, "Wall"],
    [{ "x": 4, "y": 5 }, { "Alien": { "color": "Purple" } }],
    [{ "x": 4, "y": 3 }, { "Alien": { "color": "Orange" } }],
    [{ "x": 7, "y": 1 }, { "House": { "color": "Purple" } }],
    [{ "x": 7, "y": 7 }, { "House": { "color": "Orange" } }]
  ]
}
```

Can be loaded with just this:

```rust
let stdin = io::stdin().lock();
let definition: CosmicExpressDefinition = serde_json::from_reader(stdin).unwrap();
```

But... I did change the model slightly between version 1 and here, so I had to also convert a bit:

```rust
// Convert to a global and local

// There is a hidden wall under all aliens and houses
// TODO: Entities should have an is_wall property or something
let walls = definition.entities.iter().map(|(p, _)| *p).collect();

assert!(definition.entrances.len() == 1);
assert!(definition.exits.len() == 1);

let global = CosmicExpressGlobal {
    width: definition.width,
    height: definition.height,
    length: definition.length,
    entrance: *definition.entrances.first().unwrap(),
    exit: *definition.exits.first().unwrap(),
    walls,
};

let seats = (0..definition.length).map(|_| None).collect();
let seat_goop = (0..definition.length).map(|_| false).collect();

let aliens: Vec<(Point, Color)> = definition
    .entities
    .iter()
    .filter_map(|(p, e)| {
        if let Entity::Alien { color } = e {
            Some((*p, *color))
        } else {
            None
        }
    })
    .collect();

let houses: Vec<(Point, Color)> = definition
    .entities
    .iter()
    .filter_map(|(p, e)| {
        if let Entity::House { color } = e {
            Some((*p, *color))
        } else {
            None
        }
    })
    .collect();

// Validity checks
{
    // Counts of each color alien and house match
    let mut alien_colors = aliens.iter().map(|(_, c)| c).collect::<Vec<_>>();
    alien_colors.sort();

    let mut house_colors = houses.iter().map(|(_, c)| c).collect::<Vec<_>>();
    house_colors.sort();

    assert_eq!(
        alien_colors, house_colors,
        "Alien and house counts don't match: {alien_colors:?} {house_colors:?}"
    );

    // No entities (from the original definition) overlap
    let mut points = FxHashSet::default();
    for (p, _) in definition.entities.iter() {
        assert!(points.insert(*p), "Entities overlap at {p:?}");
    }

    // The entrances and exits are all unique
    let mut points = FxHashSet::default();
    for p in definition.entrances.iter().chain(definition.exits.iter()) {
        assert!(points.insert(*p), "Entrance/exit overlap {p:?}");
    }
}

let local = CosmicExpressLocal {
    path: vec![global.entrance],
    seats,
    seat_goop,
    aliens,
    houses,
};
```

Not bad though!

## Parameterizing the solver

One thing I did for this puzzle that I hadn't otherwise done was to use [lazy_static](https://docs.rs/lazy_static/latest/lazy_static/) to load several possible `env` variables:

```rust
lazy_static! {
    static ref DEBUG_PRINT: bool = std::env::var("COSMIC_EXPRESS_DEBUG_PRINT").is_ok();
    static ref FLOODFILL_VALIDATOR: bool =
        std::env::var("COSMIC_EXPRESS_FLOODFILL_VALIDATOR").is_ok();
    static ref HEURISTIC_COUNT_ENTITIES: bool =
        std::env::var("COSMIC_EXPRESS_HEURISTIC_COUNT_ENTITIES").is_ok();
    static ref HEURISTIC_NEAREST_HOUSE: bool =
        std::env::var("COSMIC_EXPRESS_HEURISTIC_NEAREST_HOUSE").is_ok();
    static ref HEURISTIC_HUG_WALLS: bool =
        std::env::var("COSMIC_EXPRESS_HEURISTIC_HUG_WALLS").is_ok();
    static ref USE_CUSTOM_HASH: bool = std::env::var("COSMIC_EXPRESS_CUSTOM_HASH").is_ok();
}
```

In order:

* `DEBUG_PRINT` - prints out debug information, I could have just used env_logger, but this also avoids calculating the thing to print
  * TODO: Can logger take in a closure? 
* `FLOODFILL_VALIDATOR` - see [floodfill validator](#floodfill-validator); I almost always use this one
* `HEURISTIC_COUNT_ENTITIES` - my simple original heuristic; doesn't work very well
* `HEURISTIC_NEAREST_HOUSE` - see [a simple heuristic](#a-simple-heuristic)
* `HEURISTIC_HUG_WALLS` - an experimental heuristic that attempted to solve the puzzle as I would; didn't really work
* `USE_CUSTOM_HASH` - see [a custom hash](#a-custom-hash-function)

### A simple heuristic

So how were these each implemented? Well, first, I want a heuristic that will make A* behave better:

* Guess at the following distances:
  * Add the distance to the nearest alien
  * Add the distance between each alien and the closest house
  * Add the distance to the exit once we're out of aliens

It's a bit more than free to calculate, but it does make the program behave much better, so I almost always have it on. 

```rust
let current_point = self.path.last().unwrap();

// Distance from the path to the nearest remaining alien
if let Some(distance) = self
    .aliens
    .iter()
    .map(|(alien_point, _)| alien_point.manhattan_distance(*current_point))
    .min()
{
    heuristic += distance as i64;
}

// Distance from each alien to the closest matching house
for (alien_point, alien_color) in self.aliens.iter() {
    let nearest_house = self
        .houses
        .iter()
        .filter(|(_, house_color)| house_color == alien_color)
        .map(|(house_point, _)| alien_point.manhattan_distance(*house_point))
        .min();

    if let Some(distance) = nearest_house {
        heuristic += distance as i64;
    }
}

// Also, distance to the exit if we're out of aliens
heuristic += current_point.manhattan_distance(global.exit) as i64;
```

### Floodfill validator

Next up, vastly improve the `is_valid` function:

```rust
impl State<CosmicExpressGlobal, ()> for CosmicExpressLocal {
    fn is_valid(&self, g: &CosmicExpressGlobal) -> bool {
        // ...

        // Flood fill from the current head, stopping at all walls and current path
        // If we can't reach all remaining aliens, houses, and the exit
        if *FLOODFILL_VALIDATOR {
            let max_size = (g.width * g.height) as usize;

            let mut reachable = FxHashSet::default();
            reachable.reserve(max_size);

            let mut to_check = Vec::with_capacity(max_size);
            to_check.push(*self.path.last().unwrap());

            // All points current under a seat are reachable
            // This took a while to track down
            self.path
                .iter()
                .rev()
                .take(1 + self.seats.len())
                .for_each(|p| {
                    reachable.insert(*p);
                });

            // Flood fill from the head of the current path
            while let Some(p) = to_check.pop() {
                reachable.insert(p);

                // Flood fill all empty points
                for neighbor in p.neighbors().into_iter() {
                    // Only check each point once
                    if reachable.contains(&neighbor) || to_check.contains(&neighbor) {
                        continue;
                    }

                    // Don't add points out of bounds (remember there's a border)
                    if neighbor.x < 1
                        || neighbor.y < 1
                        || neighbor.x > g.width
                        || neighbor.y > g.height
                    {
                        continue;
                    }

                    // Keep expanding empty points
                    if !(g.walls.contains(&neighbor) || self.path.contains(&neighbor)) {
                        to_check.push(neighbor);
                    }
                }
            }

            // Expand all points by one: any alien or house *adjacent* to a reachable point is also reachable
            let mut expanded = FxHashSet::default();
            expanded.reserve(max_size);

            for p in reachable.iter() {
                expanded.insert(*p);
                for neighbor in p.neighbors().into_iter() {
                    expanded.insert(neighbor);
                }
            }
            let reachable = expanded;

            // All aliens and houses must be reachable
            if self.aliens.iter().any(|(p, _)| !reachable.contains(p)) {
                return false;
            }
            if self.houses.iter().any(|(p, _)| !reachable.contains(p)) {
                return false;
            }

            // At least one exit must be reachable
            if !reachable.contains(&g.exit) {
                return false;
            }
        }

        // All validators passed
        true
    }
}
```

This is fairly expensive to calculate. To the point that you can actually see it generating and checking solutions noticeably slower. But conversely, it *really* cuts down on the number of states to check. 

Basically, if the current path cuts off part of the level with an alien or house (since you can't cross over the path), you can no longer solve the puzzle. To calculate that, flood fill out from the head of the path and find all neighboring aliens/houses. 

Pretty neat and made some levels much more solvable!

### A custom hash function

Finally, an attempt that I was working on (but that didn't *really* go anywhere): a custom hashing function for `CosmicExpressLocal`:

```rust
impl Hash for CosmicExpressLocal {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        if *USE_CUSTOM_HASH {
            // Getting to exactly the same points a different way counts as equal
            // So long as the last step (where we'll expand from) is the same
            let mut path = self.path.clone();
            let last = path.pop().unwrap();

            path.sort();
            path.push(last);
            path.hash(state);

            // We don't care about which aliens since they don't move, just the list of remaining points
            // Sort so order is preserved
            let mut entities = Vec::with_capacity(self.aliens.len() + self.houses.len());
            for (p, _) in self.aliens.iter() {
                entities.push(p);
            }
            for (p, _) in self.houses.iter() {
                entities.push(p);
            }
            entities.sort();
            entities.hash(state);

            self.seats.hash(state);
            self.seat_goop.hash(state);
        } else {
            // Default hashing
            self.path.hash(state);
            self.seats.hash(state);
            self.seat_goop.hash(state);
            self.aliens.hash(state);
            self.houses.hash(state);
        }
    }
}
```

Basically (as it says in the comments), the idea here is I don't actually care how we get to a specific path, so long as we've covered the same elements in the path. So instead of hashing the path in order, we sort it then hash. Same with entities (since they don't move, just get removed). 

This... didn't actually help that much. But it was a neat idea, so I thought I'd include it!

## Current progress

```bash
$ cargo build --release --bin cosmic-express; \
testit \
  --command "./target/release/cosmic-express" \
  --env COSMIC_EXPRESS_FLOODFILL_VALIDATOR=true \
  --env COSMIC_EXPRESS_HEURISTIC_NEAREST_HOUSE=true \
  --files "data/cosmic-express/*/*.json" \
  --timeout 10

    Finished `release` profile [optimized + debuginfo] target(s) in 0.03s
data/cosmic-express/Andromeda/Andromeda 1.json: New success:

 ........
 ........
 .#......
[────────]
 ......#.
 ........
 ........

===

# ... rest of levels here ...

===

data/cosmic-express/Vela/Vela 5.json: New success:
  ]     [
 .│┌───┐│.
 .└┘.┌─┘│.
 ..##│##│.
 ..#.└┐#│.
 .┌──┐│┌┘.
 #│#.└┘│.#
 #│##.#│#.
 .│#...└┐.
 .└─────┘.

===

data/cosmic-express/Vela/Vela 6.json: Timeout
data/cosmic-express/Vela/Vela 7.json: Timeout
data/cosmic-express/Vela/Vela 8.json: Timeout

Summary:
	Successes: 26 (26 new)
	Failures: 0
	Timeouts: 27
```

Well, I've solved 26 levels so far! Actually 30 if I increase the timeout somewhat. But there are still dozens of levels that even with a significant timeout, I can't solve. It really comes down to the branching factor. The larger the level (and to a lesser extent, the more aliens I have to find), the worse it is and the longer it takes. 

Plus, this is only solutions for Andromeda, Delphinus, Ursa Minor, Vela, and a start on Cassiopeia. There are at least 5 constellations left! 

So far, I've implemented: 

* Simple trains
* Multiple cars (only up to 2 so far)
* Three alien species:
  * Orange/Purple are normal
  * After a Green sits in a seat no other can ()

But at a quick look, I still need to deal with:

* 'Any' hoses (which can take any color alien)
* Warp portals (go in one, come out the other)
* Even bigger levels!
* Cross tracks (built in to the level)
* Completion requirements 
  
Looks like fun!

But for now, we have some progress. I'll probably keep working on this. Perhaps a part 2!

Onward!