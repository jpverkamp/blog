---
title: "AoC 2022 Day 19: Blueprintinator"
date: 2022-12-19 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Algorithms
- Backtracking
- Optimization
---
## Source: [Not Enough Minerals](https://adventofcode.com/2022/day/19)

## Part 1

> Given a series of given a series of `blueprints`, each of which gives instructions for how to build a single `robot` from a collection of `materials` that in turn will produce one of a given `material` per turn, determine the best order of builds to maximize your `geode` (the most valuable `material`) production for each `blueprint` given a time limit of `24 minutes`. 

<!--more-->

Neat! I went a few different ways for this one, trying to make a more general solution at first that could handle multiple different ways to make each robot, but ... that wasn't actually necessary. There are always exactly 4 resources and always exactly 4 kinds of robots that make them (one for each). So let's do that. 

To start out, I'm going to create some aliases for types, mostly so I can change how much memory I'm using:

```rust
type ID = u16;
type Qty = u16;
type Qtys = [Qty; Material::COUNT];

fn make_qtys() -> Qtys {
    [0; Material::COUNT]
}
```

Also a helper function to make our main data structure, a `Qtys`, which is (in this case) a `[Qty; 4]`:

```rust
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
enum Material {
    Ore = 0,
    Clay = 1,
    Obsidian = 2,
    Geode = 3,
}

impl Material {
    const COUNT: usize = 4;
}

impl From<String> for Material {
    fn from(s: String) -> Self {
        match s.to_lowercase().as_str() {
            "ore" => Material::Ore,
            "clay" => Material::Clay,
            "obsidian" => Material::Obsidian,
            "geode" => Material::Geode,
            _ => panic!("unknown material {s}"),
        }
    }
}
```

I would rather be able to have something that automatically tells me how many options there actually are for an enum and it seems that there are crates that do that... but for now, this works well enough. 

Next, up actually making the robots. So interestingly, I don't actually need to store the output, since the robots will always be in order, their index is actually the same as the input (that's why I put the values in the enum). So a robot is just:

```rust
#[derive(Clone, Debug)]
struct Robot {
    inputs: Qtys,
}
```

Not bad. Next up, the main parsing function for `Blueprint`:

```rust
#[derive(Debug)]
struct Blueprint {
    id: ID,
    robots: Vec<Robot>,
}

impl From<String> for Blueprint {
    fn from(line: String) -> Self {
        let id = line
            .split_ascii_whitespace()
            .nth(1)
            .expect("must have id")
            .strip_suffix(":")
            .expect("ID ends with :")
            .parse::<ID>()
            .expect("ID must be numeric");

        let re = Regex::new(r"Each (\w+) robot costs (.*?)\.").expect("regex creation failed");

        let robots = re
            .captures_iter(&line)
            .map(|definition| {
                let mut inputs = make_qtys();

                definition[2].split(" and ").for_each(|each| {
                    let (qty, mat) = each
                        .split_ascii_whitespace()
                        .collect_tuple()
                        .expect("must have qty and material");

                    let mat = Material::from(String::from(mat));
                    let qty = qty.parse::<Qty>().expect("qty must be numeric");

                    inputs[mat as usize] += qty;
                });

                Robot { inputs }
            })
            .collect::<Vec<_>>();

        Blueprint { id, robots }
    }
}
```

This time around I'm using [[wiki:regular expressions]]() for parsing, which works out pretty well. I feel like my parsing is at least growing and changing. Whether it's idiomatic Rust... that I'm not quite so sure about. 

Now, for the actual solver, we're going to use the same general idea as I finally ended up using in [[wiki:AoC 2022 Day 16: Pressurinator]](). Create a stack of solutions and then for each step, bail out if it's worse than some possible upper bound, otherwise generate each possible next step. I really should implement an [[wiki:A* solver]]() instead... but this works. And it's close. 

Okay, the solver. It's certainly getting longer:

```rust
impl Blueprint {
    fn solve(&self, max_time: usize) -> (u16, Vec<Option<u16>>) {
        #[derive(Clone, Debug)]
        struct State {
            time: u16,
            inventory: Qtys,
            population: Qtys,
            builds: Vec<Option<ID>>,
        }

        let mut queue = Vec::new();

        // Generate the initial state, no inventory but one of each material
        let inventory = make_qtys();
        let mut population = make_qtys();
        population[0] = 1;
        queue.push(State {
            time: max_time as Qty,
            inventory,
            population,
            builds: Vec::new(),
        });

        // Best case is # of geodes + the build order to get there
        let mut best = (0 as ID, Vec::new());

        while !queue.is_empty() {
            let State {
                time,
                inventory,
                population,
                builds,
            } = queue.pop().unwrap();
            count += 1;

            let geode_qty = inventory[Material::Geode as usize];
            if geode_qty > best.0 {
                best = (geode_qty, builds.clone());
            }

            if time == 0 {
                continue;
            }

            // Best case: build a new geode robot each frame (ignore inputs)
            let best_case_geodes =
                geode_qty + population[Material::Geode as usize] * time + time * (time + 1) / 2;
            if best_case_geodes < best.0 {
                skip_count += 1;
                continue;
            }

            // For each kind of robot, try to build it next
            for (id, robot) in self.robots.iter().enumerate() {
                // It's impossible to build, we don't make the right resources
                if robot
                    .inputs
                    .iter()
                    .enumerate()
                    .any(|(input_id, input_qty)| *input_qty > 0 && population[input_id] == 0)
                {
                    continue;
                }

                // When is the next time we'll have enough inputs to build it?
                let ticks = robot
                    .inputs
                    .iter()
                    .enumerate()
                    .map(|(input_id, input_qty)| {
                        if inventory[input_id] >= *input_qty {
                            0
                        } else {
                            ((*input_qty - inventory[input_id]) as f32
                                / population[input_id] as f32)
                                .ceil() as Qty
                        }
                    })
                    .max()
                    .unwrap()
                    + 1;

                // If it won't be done in time, don't try to
                if ticks > time {
                    continue;
                }

                // Update inventory for those ticks - this build
                let mut new_inventory = inventory.clone();

                population
                    .iter()
                    .enumerate()
                    .for_each(|(id, qty)| new_inventory[id] += *qty * ticks);

                self.robots[id]
                    .inputs
                    .iter()
                    .enumerate()
                    .for_each(|(id, qty)| new_inventory[id] -= *qty);

                // Update the population with the new robot
                let mut new_population = population.clone();
                new_population[id] += 1;

                // Update the steps with the number of skips + the build
                let mut new_builds = builds.clone();
                for _ in 0..(ticks - 1) {
                    new_builds.push(None);
                }
                new_builds.push(Some(id as ID));

                // Add to queue
                queue.push(State {
                    time: time - ticks,
                    inventory: new_inventory,
                    population: new_population,
                    builds: new_builds,
                });
            }
        }

        best
    }
}
```

It's pretty much the same code as what I ended up with for day 16 and I hope well enough commented. The interesting bits are:

* The initial state starts with no inventory and 1 of the lowest level (ore-collecting) robot
* The best case is how many geodes we built
* This time I wrapped everything up in an internal `State` structure; it's neat being able to define these within a function
* The best case assumes you can build a `geode` robot each frame for the rest of the game (without checking input), each of which produces a `geode` until the end of the simulation. This uses the [[wiki:1 + 2 + 3 + 4 + ⋯]]() formula to calculate quickly. It only removes the worst cases, but that's really all we need
* The recursive case tries to build one of each robot:
  * If we don't even produce the right resources, don't try to calculate it 
  * Otherwise, figure out how many ticks it will take to build it, schedule the build for then. This is perhaps the most interesting bit: rather than recurring once every time increment, we skip forward long enough to build the next bot. This helps cut down the search time significantly. 
  * Update the inventory to: produce whatever we do * time + use the resources to build the new bot
  * Update the population with the new bot

And that's basically it. To solve the problem, load each `Blueprint` and find the total quality as requested:

```rust
fn part1(filename: &Path) -> String {
    let blueprints = iter_lines(filename)
        .map(Blueprint::from)
        .collect::<Vec<_>>();

    let mut total_quality = 0;

    for blueprint in blueprints.into_iter() {
        let (geode_count, steps) = blueprint.solve(24);
        total_quality += blueprint.id * geode_count;
    }

    total_quality.to_string()
}
```

Cool. 

## Part 2

> Do the same thing with a time limit of `32 minutes`, but only for the first 3 blueprints. Calculate the product of their `geode` production numbers. 

This is quite literally the same thing. If you code isn't as good, it would certainly take a very very long time if you were doing this less efficiently. 

```rust
fn part2(filename: &Path) -> String {
    let blueprints = iter_lines(filename)
        .map(Blueprint::from)
        .take(3) // Only keep the first 3 blueprints
        .collect::<Vec<_>>();

    let mut quality_product = 1;

    for blueprint in blueprints.into_iter() {
        let (geode_count, steps) = blueprint.solve(32);
        quality_product *= geode_count;
    }

    quality_product.to_string()
}
```

The iterator functions (`take` in this example) being core to the language is so nice. 

## Performance

So... it's not fast. But I was really working more towards getting things working at this point. 

```bash
$ ./target/release/19-blueprintinator 1 data/19.txt

1092
took 8.854342166s

$ ./target/release/19-blueprintinator 2 data/19.txt

3542
took 155.567067083s
```

I really would much rather get that under a minute, but for the moment... I'm moving on!

## Edit Dec 25, Optimizing Max Builds

So On digging back into this problem (my longest by far), I did come up with one (pretty major) improvement: 

We can only build one robot per turn. So the most resources we'll ever need per turn is the maximum of that resource to build any robot. Once we've built that many, stop building that kind of robot. This will mostly stop looking down branches where we build the smallest robots. 

Implementation wise, there are only two small changes:

1. At the top of the loop before processing the `queue`:

    ```rust
    // Figure out the most of each resource we need to build any given robot
    // We don't need more than that many production robots, since you can only build one per frame
    let mut max_needed = (0..Material::COUNT)
        .map(|i| self.robots.iter().map(|r| r.inputs[i]).max().unwrap())
        .collect::<Vec<_>>();
    max_needed[Material::Geode as usize] = Qty::MAX;
    ```

2. In the loop before even checking if it's possible to build one:

    ```rust
    // We don't need any more of this one
    if id != (Material::Geode as Qty) {
        // We are creating enough resources each tick to build any robot
        if population[id] >= max_needed[id] {
            continue;
        }
    }
    ```

And that's really it. The results are ... 

```bash
$ ./target/release/19-blueprintinator 1 data/19.txt

1092
took 262.607583ms

$ ./target/release/19-blueprintinator 2 data/19.txt

3542
took 1.928983666s
```

That's really impressive. Roughly ~80x faster. That actually brings this down to 4th slowest, faster than Day [16]({{<ref "2022-12-16-pressurinator.md">}}), [23]({{<ref "2022-12-23-elf-scattinator">}}.md), and [24]({{<ref "2022-12-24-blizzinator.md">}}). It's amazing what you can do with just a few lines of code...