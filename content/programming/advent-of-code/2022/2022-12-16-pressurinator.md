---
title: "AoC 2022 Day 16: Pressurinator"
date: 2022-12-16 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Proboscidea Volcanium](https://adventofcode.com/2022/day/16)

## Part 1

> Given a graph of nodes, some of which have a `pressure` (per tick output value) and an agent that can move through the graph and activate specific nodes (so that they output their per tick value every future tick), what is the maximum total output possible in 30 steps? 

<!--more-->

Oooh, that's fun. I took a *long* time optimizing this one over and over again to get it to actually solve even part 1. I have to admit... I don't actually have a part 2 solution yet that will run in a reasonable amount of time (and more importantly with a reasonable amount of RAM). I'll update this post when I do...

But in any case, on to the solution. 

As always, the first goal is to store the cave:

```rust
// Store the description of the cave as a directed graph with flow rates at the nodes
#[derive(Debug)]
struct Cave {
    size: usize,
    names: Vec<String>,
    indexes: HashMap<String, usize>,
    flow_rates: Vec<usize>,
    distances: Matrix<usize>,
}
```

We're using the `Matrix` class we defined earlier, otherwise nothing out of the ordinary. Parsing uses the regex tricks from yesterday:

```rust
// Parse a graph from a string iterator
impl<I> From<&mut I> for Cave
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        let mut names = Vec::new();
        let mut indexes = HashMap::new();
        let mut flow_rates = Vec::new();
        let mut neighbors = HashMap::new();

        let re = Regex::new(
            r"Valve (\w+) has flow rate=(\d+); tunnels? leads? to valves? ((?:\w+)(?:, \w+)*)",
        )
        .expect("regex creation failed");

        for (index, line) in iter.enumerate() {
            let caps = re.captures(&line).expect("regex doesn't match line");
            let name = String::from(&caps[1]);

            neighbors.insert(
                name.clone(),
                caps[3]
                    .split(", ")
                    .map(|s| (1, String::from(s)))
                    .collect::<Vec<_>>(),
            );

            indexes.insert(name.clone(), index);
            names.push(name);
            flow_rates.push(caps[2].parse::<usize>().unwrap());
        }

        let size = names.len();

        // Write distances as a matrix
        let mut distances = Matrix::<usize>::new(size, size);

        for i in 0..size {
            for j in 0..size {
                distances[[i, j]] = usize::MAX;
            }
        }

        for (src, neighbors) in neighbors.iter() {
            for (distance, dst) in neighbors.iter() {
                distances[[indexes[src], indexes[dst]]] = *distance;
            }
        }
        
        Cave {
            size: names.len(),
            names,
            indexes,
            flow_rates,
            distances,
        }
    }
}
```

So originally, I define a single step as:

* moving between any two connected nodes
* enabling the current node

There's a much better way to do this, but we'll come back to that. 

The basic idea of the original solution was:

* Define a function `recur` that takes in the current location, remaining fuel, and which locations are enabled
* Calculate a base case result of doing nothing for the rest of the simulation (`result`)
* If the current location isn't enabled, fire off a `recur`sive solution that does an `Enable` step now and then finds the best recursive solution; if this is better than `result`, it becomes `result`
* For each neighboring node, do the same, calculate `recur` for `Move(node)` and if the recursive solution there is better, then take that result

Technically correct... but very slow. I don't actually even have runtimes for this one. 

I did have one way that I could at least make it bearable though: {{<wikipedia memoization>}}. Essentially, cache the result of each recursive call, that way if I end up in the same state through another branch (such as if A -> B -> C, A -> D -> C, then moving down either path results in the same `recur` calls.)

To implement that, I added this to my `max_flow` function:

```rust
// Flow algorithms for a cave
impl Cave {
    // Find the steps for maximizing flow from a single location with a single agent
    fn max_flow(self, location: String, fuel: usize) -> (usize, Vector<Step>) {
        type CacheKey = (usize, usize, Vector<bool>);
        type CacheValue = (usize, Vector<Step>);

        // The memoized recursive function that actually does the work
        // cave and cache don't change
        // index is where the agent currently is
        // fuel is how much fuel is left in the simulation (stop at 0)
        // enabled is a list of which cave pumps are currently enabled
        fn recur(
            cave: Rc<Cave>,
            cache: Rc<RefCell<HashMap<CacheKey, CacheValue>>>,
            index: usize,
            fuel: usize,
            enabled: Vector<bool>,
        ) -> CacheValue {
            // If we have already calculated a result at this index/fuel/enabled, return it
            let cache_key = (index, fuel, enabled.clone());
            if cache.borrow().contains_key(&cache_key) {
                return cache.borrow_mut()[&cache_key].clone();
            }

            ...


            // Store the result in the cache and return it
            cache.borrow_mut().insert(cache_key, result.clone());
            result
        }

        // Fire off the recursive function
        let cave = Rc::new(self);
        recur(
            cave.clone(),
            Rc::new(RefCell::new(HashMap::new())),
            cave.clone().indexes[&location],
            fuel,
            Vector::from(vec![false; cave.clone().size]),
        )
    }
}
```

Don't worry, we'll get to the core of the algorithm. In a nutshell though, we pass around the `cache` (with `Rc`, so it's cheap enough) and if we've already seen the same `(index, fuel, enabled)`, we just return it. 

Does this still work? Absolutely:

```bash
[ 1] Move("DD")
[ 2] Enable
[ 3] Move("CC")
[ 4] Move("BB")
[ 5] Enable
[ 6] Move("AA")
[ 7] Move("II")
[ 8] Move("JJ")
[ 9] Enable
[10] Move("II")
[11] Move("AA")
[12] Move("DD")
[13] Move("EE")
[14] Move("FF")
[15] Move("GG")
[16] Move("HH")
[17] Enable
[18] Move("GG")
[19] Move("FF")
[20] Move("EE")
[21] Enable
[22] Move("DD")
[23] Move("CC")
[24] Enable
[25] DoNothing
[26] DoNothing
[27] DoNothing
[28] DoNothing
[29] DoNothing
[30] DoNothing
1651
took 7.661355375s
```

This isn't on my full data (with 59 nodes), this is just on the given test data (with only 10 nodes). And it already takes 7 seconds. With the full data, I think it took a few minutes to solve? Still perfectly reasonable, but... I knew I could do better.

### Optimized version with multiple steps and no-repeats

Okay, the next way I attacked the problem was to optimize the number of choices we make at any given step to keep branching under control. To do that, I wanted to do a few things:

* Improve the `distance` map. If we can get `a -> b -> c`, then we can assume we can go `a -> c` using 2 fuel. We can account for that. 
* Don't go to nodes that are already enabled; anytime we go to a node, assume we'll enable it, since the above accounts for moving through enabled nodes.
* Don't go to nodes that have 0 flow; they're functionally just connectors. 

With all of this, there are only 7 branches at first, 6 after that, 5 after that and so on. A total of {{<inline-latex "7! = 5040">}} cases instead of 10 at every step. 

Running on the test case:

```bash
./target/release/16-pressurinator 1 data/16-test.txt

Step(1, "DD")
Step(2, "BB")
Step(3, "JJ")
Step(7, "HH")
Step(3, "EE")
Step(2, "CC")
Step(4, "GG")
1651
took 40.906083ms
```

Ahyup, that's much faster. Even on the full 59 nodes, there are only 23 that have a flow rate, so {{<inline-latex "23! = 2.58 * 10^22">}}. Yeah, okay that's still a huge number. But remember the caching? Because of the relatively limited number of cases, it caches *much* better:

```bash
./target/release/16-pressurinator 1 data/16.txt

Step(2, "CA")
Step(2, "JF")
Step(3, "LE")
Step(3, "FP")
Step(2, "YH")
Step(2, "UX")
Step(2, "AR")
Step(4, "DM")
1720
took 175.448208ms
```

That... is acceptable. 

### The actual code

So... how does that work? First, expand the `from` function to calculate all distances:

```rust

// Parse a graph from a string iterator
impl<I> From<&mut I> for Cave
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        ...

        // Expand to calculate the minimum possible distance between nodes (of any number of steps)
        // For any pair of nodes, if we don't have a distance:
        // - Find a third node between them with a sum of of i->k->l == distance
        // Because distance is increasing from 2 up, this will always fill in minimal values
        loop {
            let mut changed = false;
            for i in 0..size {
                for j in 0..size {
                    for k in 0..size {
                        if i == j || j == k || i == k {
                            continue;
                        }

                        if distances[[i, j]] == usize::MAX || distances[[j, k]] == usize::MAX {
                            continue;
                        }

                        let old_d = distances[[i, k]];
                        let new_d = distances[[i, j]] + distances[[j, k]];
                        if new_d < old_d {
                            changed = true;
                            distances[[i, k]] = new_d;
                        }
                    }
                }
            }

            if !changed {
                break;
            }
        }

        Cave {
            size: names.len(),
            names,
            indexes,
            flow_rates,
            distances,
        }
    }
}
```

For each possible triple of nodes `(i, j, k)`, see if we can add a new node `i, k` distance via `j` / update the previous one with a better answer. 

Now, we can use that do show the whole algorithm:

```rust
// A single step of the single agent simulation
#[derive(Clone, Debug, Hash, Eq, PartialEq, Ord, PartialOrd)]
struct Step(usize, String);

// Flow algorithms for a cave
impl Cave {
    // Find the steps for maximizing flow from a single location with a single agent
    fn max_flow(self, location: String, fuel: usize) -> (usize, Vector<Step>) {
        type CacheKey = (usize, usize, Vector<bool>);
        type CacheValue = (usize, Vector<Step>);

        // The memoized recursive function that actually does the work
        // cave and cache don't change
        // index is where the agent currently is
        // fuel is how much fuel is left in the simulation (stop at 0)
        // enabled is a list of which cave pumps are currently enabled
        fn recur(
            cave: Rc<Cave>,
            cache: Rc<RefCell<HashMap<CacheKey, CacheValue>>>,
            index: usize,
            fuel: usize,
            enabled: Vector<bool>,
        ) -> CacheValue {
            // If we have already calculated a result at this index/fuel/enabled, return it
            let cache_key = (index, fuel, enabled.clone());
            if cache.borrow().contains_key(&cache_key) {
                return cache.borrow_mut()[&cache_key].clone();
            }

            // Calculate the current flow based on the enabled gates
            let per_tick_flow = cave
                .clone()
                .flow_rates
                .iter()
                .zip(enabled.clone().iter())
                .filter_map(|(f, c)| if *c { Some(*f) } else { None })
                .sum::<usize>();

            // Base case: try doing nothing for the rest of the simulation
            let mut result = (fuel * per_tick_flow, Vector::new());

            // Try each possible move
            // A move is move to a node (inc multiple hops) + enable that node
            for next_index in 0..cave.clone().size {
                // Don't bother moving to something that's already on
                // Don't bother moving to nodes with 0 flow
                if index == next_index
                    || enabled[next_index]
                    || cave.clone().flow_rates[next_index] == 0
                {
                    continue;
                }

                // Calculate the distance to this new node
                // If we don't have enough fuel to make that trip, this isn't valid
                let d = cave.clone().distances[[index, next_index]];
                if d + 1 > fuel {
                    continue;
                }

                // Calculate which nodes will be enabled after this step
                let mut next_enabled = enabled.clone();
                next_enabled[next_index] = true;

                // Recursively calculate the result from taking this step
                let mut sub_result = recur(
                    cave.clone(),
                    cache.clone(),
                    next_index,
                    fuel - d - 1,
                    next_enabled,
                );

                // Update that result with the total flow from moving
                // And the instruction for output
                sub_result.0 += (d + 1) * per_tick_flow;
                sub_result
                    .1
                    .push_front(Step(d, cave.clone().names[next_index].clone()));

                // If that result is better than what we have so far, update our best result
                result = result.max(sub_result);
            }

            // Store the result in the cache and return it
            cache.borrow_mut().insert(cache_key, result.clone());
            result
        }

        // Fire off the recursive function
        let cave = Rc::new(self);
        recur(
            cave.clone(),
            Rc::new(RefCell::new(HashMap::new())),
            cave.clone().indexes[&location],
            fuel,
            Vector::from(vec![false; cave.clone().size]),
        )
    }
}
```

Everything is basically as I described above: 

* Start with doing nothing
* For each remaining neighbor:
  * If it's not the current node
  * AND if it's not already enabled
  * AND if it has a non-zero flow rate
  * AND if we have enough fuel to get there
  * Then we `recur` down that branch and use the best of these results

That's really it. 

One oddity is that there are a ton of `clone()` all over the place. This is actually perfectly fine, since I'm doing `clone()` on `Rc`. That basically means I'm making a new pointer to the same data structure and keeping track of all of them. There's some small overhead, but it keeps Rust happy. 

Optimally, I would have preferred to make this a closure with a single `cave` and `cache` captured from the environment instead, but this works well enough. I suppose making a new struct with `cave` and `cache` on the struct and `recur` as a method on it would have worked as well. C'est la vide. 

### Attempted to solve via 30 steps of all possibilities

As a quick aside, for a while, I tried a parallel approach where I would start in each state and then keep track of the 'best' way to get into each state for each step. The problem is, this doesn't include the cases of both moving through a node and enabling it and not. So it's not actually capable of optimizing this particular problem. 

```bash
Tick 0
	[state 0=AA] State(total: 0, current: 0, steps: [])
	[state 1=BB] None
	[state 2=CC] None
	[state 3=DD] None
	[state 4=EE] None
	[state 5=FF] None
	[state 6=GG] None
	[state 7=HH] None
	[state 8=II] None
	[state 9=JJ] None

Tick 1
	[state 0=AA] State(total: 0, current: 0, steps: [Enable])
	[state 1=BB] State(total: 0, current: 0, steps: [Move(1, "BB")])
	[state 2=CC] None
	[state 3=DD] State(total: 0, current: 0, steps: [Move(1, "DD")])
	[state 4=EE] None
	[state 5=FF] None
	[state 6=GG] None
	[state 7=HH] None
	[state 8=II] State(total: 0, current: 0, steps: [Move(1, "II")])
	[state 9=JJ] None

Tick 2
	[state 0=AA] State(total: 0, current: 0, steps: [Move(1, "II"), Move(1, "AA")])
	[state 1=BB] State(total: 0, current: 13, steps: [Move(1, "BB"), Enable])
	[state 2=CC] State(total: 0, current: 0, steps: [Move(1, "DD"), Move(1, "CC")])
	[state 3=DD] State(total: 0, current: 20, steps: [Move(1, "DD"), Enable])
	[state 4=EE] State(total: 0, current: 0, steps: [Move(1, "DD"), Move(1, "EE")])
	[state 5=FF] None
	[state 6=GG] None
	[state 7=HH] None
	[state 8=II] State(total: 0, current: 0, steps: [Enable, Move(1, "II")])
	[state 9=JJ] State(total: 0, current: 0, steps: [Move(1, "II"), Move(1, "JJ")])

Tick 3
	[state 0=AA] State(total: 20, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "AA")])
	[state 1=BB] State(total: 13, current: 13, steps: [Move(1, "BB"), Enable, DoNothing])
	[state 2=CC] State(total: 20, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "CC")])
	[state 3=DD] State(total: 20, current: 20, steps: [Move(1, "DD"), Enable, DoNothing])
	[state 4=EE] State(total: 20, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "EE")])
	[state 5=FF] State(total: 0, current: 0, steps: [Move(1, "DD"), Move(1, "EE"), Move(1, "FF")])
	[state 6=GG] None
	[state 7=HH] None
	[state 8=II] State(total: 0, current: 0, steps: [Move(1, "II"), Move(1, "JJ"), Move(1, "II")])
	[state 9=JJ] State(total: 0, current: 21, steps: [Move(1, "II"), Move(1, "JJ"), Enable])

Tick 4
	[state 0=AA] State(total: 40, current: 20, steps: [Move(1, "DD"), Enable, DoNothing, Move(1, "AA")])
	[state 1=BB] State(total: 40, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "CC"), Move(1, "BB")])
	[state 2=CC] State(total: 40, current: 22, steps: [Move(1, "DD"), Enable, Move(1, "CC"), Enable])
	[state 3=DD] State(total: 40, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Move(1, "DD")])
	[state 4=EE] State(total: 40, current: 23, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Enable])
	[state 5=FF] State(total: 40, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Move(1, "FF")])
	[state 6=GG] State(total: 0, current: 0, steps: [Move(1, "DD"), Move(1, "EE"), Move(1, "FF"), Move(1, "GG")])
	[state 7=HH] None
	[state 8=II] State(total: 40, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "AA"), Move(1, "II")])
	[state 9=JJ] State(total: 21, current: 21, steps: [Move(1, "II"), Move(1, "JJ"), Enable, DoNothing])

Tick 5
	[state 0=AA] State(total: 60, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "AA"), Move(1, "II"), Move(1, "AA")])
	[state 1=BB] State(total: 62, current: 22, steps: [Move(1, "DD"), Enable, Move(1, "CC"), Enable, Move(1, "BB")])
	[state 2=CC] State(total: 62, current: 22, steps: [Move(1, "DD"), Enable, Move(1, "CC"), Enable, DoNothing])
	[state 3=DD] State(total: 63, current: 23, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Enable, Move(1, "DD")])
	[state 4=EE] State(total: 63, current: 23, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Enable, DoNothing])
	[state 5=FF] State(total: 63, current: 23, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Enable, Move(1, "FF")])
	[state 6=GG] State(total: 60, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "EE"), Move(1, "FF"), Move(1, "GG")])
	[state 7=HH] State(total: 0, current: 0, steps: [Move(1, "DD"), Move(1, "EE"), Move(1, "FF"), Move(1, "GG"), Move(1, "HH")])
	[state 8=II] State(total: 60, current: 20, steps: [Move(1, "DD"), Enable, DoNothing, Move(1, "AA"), Move(1, "II")])
	[state 9=JJ] State(total: 60, current: 20, steps: [Move(1, "DD"), Enable, Move(1, "AA"), Move(1, "II"), Move(1, "JJ")])
```



## Part 2

> Do the same only with two agents and 26 steps. 

Now this is where things really got complicated. In a nutshell, I started out writing it with two `index` values plus adding a `ttl` value for each so that I knew how far along a given path we were. For that to work, I had essentially 4 blocks in my 'choose which `recur`' function:

* If either agent had a `ttl = 0`, they needed to choose where to go next. 

    This was done the same way as above (try each node that isn't `enabled` and has a `flow_rate > 0`), I would set the `ttl = distance + 1`, since it would take `distance` to get to the node and `1` more to `enable` it. 

    The interesting bit of this one was that this branch *didn't* actually use any fuel. It changed the agent, but because it didn't use any fuel, I could do two of these (one for each agent) before moving on without breaking anything. 

* If either agent had a `ttl = 1`, they were at a node and needed to `enable` it. 

    This I did in a single case where I looped over all of the active agents and found all of them with `ttl = 1`, setting `enable` for all of them at once, then advancing 1 fuel for them and all the rest. This is also where I updated the flow (since flow doesn't happen until the tick after an `enable` this works). This would put any with `ttl = 1` into the `ttl = 0` case for the next tick.

    I did have to do this one all at once, because I can't just tick some agents and not others, all agents had to tick at once. 

    One interesting thing is that this case only had one possible `recur` (advance by 1 + set some `enabled` flags). We'll come back to an implication of that in a bit. 

* Finally, if all `ttl > 1`, then we could advance time until we get to the `ttl = 1` case. So find the minimum ttl and advance by `minimum(ttl) - 1`. This just adds the current flow to the total and otherwise doesn't branch (like the above case).

Now this worked, but I was getting some odd bugs and the code was annoying to reason about. So what I really wanted was something a bit more elegant. 

### Simulating *n* agents

Enter the `n-agent` simulation. Instead of 2, we could have any number... even 1. For this, I made a `State` struct which contained the above `index` and `ttl`:

```rust
// The state of an agent in the multi agent simulation
#[derive(Copy, Clone, Debug, Hash, Eq, PartialEq)]
struct State {
    index: usize,
    ttl: usize,
}

impl State {
    fn new(index: usize) -> State {
        State { index, ttl: 0 }
    }

    fn tick(self, ticks: usize) -> State {
        State {
            index: self.index,
            ttl: self.ttl - ticks,
        }
    }
}
```

Now the `max_flow_multi` function looks like this:

```rust
impl Cave {
    // The same simulation but with multiple agents
    fn max_flow_multi(
        self,
        location: String,
        fuel: usize,
        agents: usize,
    ) -> (usize, Vec<StepMulti>) {
        type CacheKey = (Vec<State>, usize, BitVec);
        type CacheValue = (usize, Vec<StepMulti>);

        // Main recursive function with multiple agents
        // cave and cache still don't change (other than to cache values)
        // agents is an im::Vector of agent states, can be any number (even 1)
        // - this contains the next index
        // - plus a new value ttl which is how long it will take the agent to get to the index
        // fuel is how long the simulation can still run
        // enabled is the map of which flows are enabled
        fn recur(
            cave: Rc<Cave>,
            cache: Rc<RefCell<HashMap<CacheKey, CacheValue>>>,
            agents: Vector<State>,
            fuel: usize,
            enabled: Vector<Bool>,
        ) -> CacheValue {
            // Cache based on the state of all agents/fuel/enabled
            let cache_key = (agents.clone(), fuel, enabled.clone());
            if cache.borrow().contains_key(&cache_key) {
                return cache.borrow_mut()[&cache_key].clone();
            }

            ...

        }

        // Init the agents and kick the recursive function off
        let cave = Rc::new(self);
        let (total_flow, steps) = recur(
            cave.clone(),
            Rc::new(RefCell::new(HashMap::new())),
            Vector::from(vec![State::new(cave.clone().indexes[&location]); agents]),
            fuel,
            Vector::from(vec![0; cave.clone().size]),
        );

        // Because we're using Vec, the steps end up in reverse order
        (total_flow, steps.into_iter().rev().collect::<Vec<_>>())
    }
}
```

I'm still using `Rc` + `RefCell` for the `cave` and `cache`, but this time, I'm using `im::Vector` for the agents and the `enabled` field. In theory, these data structures are able to share a low of their structure between all of the different calls, only spending memory for the changes. 

### New multi-agent code with one agent

As a first case, I want to test if this actually works with a single agent. In theory, it should, because the scheduling will always be the same:

```bash
$ cargo run --release --bin 16-pressurinator 1 data/16-test.txt

Step(1, "DD")
Step(2, "BB")
Step(3, "JJ")
Step(7, "HH")
Step(3, "EE")
Step(2, "CC")
1651
took 5.135ms

$ cargo run --release --bin 16-pressurinator 2 data/16-test.txt

Schedule { fuel: 30, agent: 0, distance: 1, target: "DD" }
AdvanceTime { fuel: 30, ticks: 1 }
EnableTick { fuel: 29, activations: [(0, "DD")] }
Schedule { fuel: 28, agent: 0, distance: 2, target: "BB" }
AdvanceTime { fuel: 28, ticks: 2 }
EnableTick { fuel: 26, activations: [(0, "BB")] }
Schedule { fuel: 25, agent: 0, distance: 3, target: "JJ" }
AdvanceTime { fuel: 25, ticks: 3 }
EnableTick { fuel: 22, activations: [(0, "JJ")] }
Schedule { fuel: 21, agent: 0, distance: 7, target: "HH" }
AdvanceTime { fuel: 21, ticks: 7 }
EnableTick { fuel: 14, activations: [(0, "HH")] }
Schedule { fuel: 13, agent: 0, distance: 3, target: "EE" }
AdvanceTime { fuel: 13, ticks: 3 }
EnableTick { fuel: 10, activations: [(0, "EE")] }
Schedule { fuel: 9, agent: 0, distance: 2, target: "CC" }
AdvanceTime { fuel: 9, ticks: 2 }
EnableTick { fuel: 7, activations: [(0, "CC")] }
DoNothing { fuel: 6 }
1651
took 3.724916ms
```

That's a good sign! And it's actually faster somehow. It's short enough that I'm not particularly worried about why for that now. So let's try 2 agents.

### Checking with multiple agents

```bash
$ cargo run --release --bin 16-pressurinator 2 data/16-test.txt

Step2 { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 0, distance: 1, target: "DD" } }
Step2 { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 1, distance: 1, target: "BB" } }
Step2 { fuel: 26, per_tick_flow: 0, data: AdvanceTime { ticks: 1 } }
Step2 { fuel: 25, per_tick_flow: 0, data: EnableTick { activations: [(0, "DD"), (1, "BB")] } }
Step2 { fuel: 24, per_tick_flow: 33, data: Schedule { agent: 0, distance: 4, target: "HH" } }
Step2 { fuel: 24, per_tick_flow: 33, data: Schedule { agent: 1, distance: 3, target: "JJ" } }
Step2 { fuel: 24, per_tick_flow: 33, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 21, per_tick_flow: 33, data: EnableTick { activations: [(1, "JJ")] } }
Step2 { fuel: 20, per_tick_flow: 54, data: Schedule { agent: 1, distance: 4, target: "CC" } }
Step2 { fuel: 20, per_tick_flow: 54, data: EnableTick { activations: [(0, "HH")] } }
Step2 { fuel: 19, per_tick_flow: 76, data: Schedule { agent: 0, distance: 3, target: "EE" } }
Step2 { fuel: 19, per_tick_flow: 76, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 16, per_tick_flow: 76, data: EnableTick { activations: [(0, "EE"), (1, "CC")] } }
Step2 { fuel: 15, per_tick_flow: 81, data: Schedule { agent: 0, distance: 4, target: "JJ" } }
Step2 { fuel: 15, per_tick_flow: 81, data: Schedule { agent: 1, distance: 5, target: "HH" } }
Step2 { fuel: 15, per_tick_flow: 81, data: AdvanceTime { ticks: 4 } }
Step2 { fuel: 11, per_tick_flow: 81, data: EnableTick { activations: [(0, "JJ")] } }
Step2 { fuel: 10, per_tick_flow: 81, data: Schedule { agent: 0, distance: 4, target: "EE" } }
Step2 { fuel: 10, per_tick_flow: 81, data: EnableTick { activations: [(1, "HH")] } }
Step2 { fuel: 9, per_tick_flow: 81, data: Schedule { agent: 1, distance: 7, target: "JJ" } }
Step2 { fuel: 9, per_tick_flow: 81, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 6, per_tick_flow: 81, data: EnableTick { activations: [(0, "EE")] } }
Step2 { fuel: 5, per_tick_flow: 81, data: Schedule { agent: 0, distance: 3, target: "HH" } }
Step2 { fuel: 5, per_tick_flow: 81, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 2, per_tick_flow: 81, data: EnableTick { activations: [(0, "HH"), (1, "JJ")] } }
Step2 { fuel: 1, per_tick_flow: 81, data: DoNothing }
1705
took 85.591208ms
```

It's still pretty *fast*, even with the much larger search space! And it works! Almost. 

But... that's not actually the right answer. It's really close, but I should be able to get a 1707 out of there instead of the 1705. 

That... took some digging, but eventually, I figured it out. There's an edge case (which this thankfully exposes) in the last non-`enabled` valve. If the two agents are not scheduling on the same tick (and they're usually not), then whichever one finishes first will get scheduled to go to this node. 

*But* what if that agent is on the completely other side of the simulation... The other agent (that finishes later) should be able to route to that index instead and leave the first one done to just do nothing instead. 

In this case, I solved it by considering a special case once the number of nodes that have a non-zero flow that are not enabled is less than the number of agents, I relax the `enabled[next_index]` check, allowing them to go to an enabled node again. Like this (I'll come back to the details for what else is going on here):

```rust
// Once all useful flows are active, allow moving to anywhere
let potential_enabled = cave
    .clone()
    .flow_rates
    .iter()
    .zip(enabled.clone())
    .filter_map(|(f, e)| if *f > 0 && !e { Some(true) } else { None })
    .count();

// If our TTL is 0, schedule our next move
// This doesn't advance time
if let Some((i, agent)) = agents.clone().iter().enumerate().find(|(_, a)| a.ttl == 0) {
    for next_index in 0..cave.clone().size {
        if agents.clone().iter().any(|a| next_inde
        if agents.clone().iter().any(|a| next_index == a.index)
            || (potential_enabled >= agents.len() && enabled[next_index])
            || cave.clone().flow_rates[next_index] == 0
        {
            continue;
        }

        ...
    }
}
```

Because it's late in the process, the performance hit is fairly minimal and more importantly, it actually generates the right answer:

```bash
$ cargo run --release --bin 16-pressurinator 2 data/16-test.txt

Step2 { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 0, distance: 2, target: "JJ" } }
Step2 { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 1, distance: 1, target: "DD" } }
Step2 { fuel: 26, per_tick_flow: 0, data: AdvanceTime { ticks: 1 } }
Step2 { fuel: 25, per_tick_flow: 0, data: EnableTick { activations: [(1, "DD")] } }
Step2 { fuel: 24, per_tick_flow: 20, data: Schedule { agent: 1, distance: 4, target: "HH" } }
Step2 { fuel: 24, per_tick_flow: 20, data: EnableTick { activations: [(0, "JJ")] } }
Step2 { fuel: 23, per_tick_flow: 41, data: Schedule { agent: 0, distance: 3, target: "BB" } }
Step2 { fuel: 23, per_tick_flow: 41, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 20, per_tick_flow: 41, data: EnableTick { activations: [(0, "BB"), (1, "HH")] } }
Step2 { fuel: 19, per_tick_flow: 76, data: Schedule { agent: 0, distance: 1, target: "CC" } }
Step2 { fuel: 19, per_tick_flow: 76, data: Schedule { agent: 1, distance: 3, target: "EE" } }
Step2 { fuel: 19, per_tick_flow: 76, data: AdvanceTime { ticks: 1 } }
Step2 { fuel: 18, per_tick_flow: 76, data: EnableTick { activations: [(0, "CC")] } }
Step2 { fuel: 17, per_tick_flow: 78, data: Schedule { agent: 0, distance: 5, target: "HH" } }
Step2 { fuel: 17, per_tick_flow: 78, data: AdvanceTime { ticks: 1 } }
Step2 { fuel: 16, per_tick_flow: 78, data: EnableTick { activations: [(1, "EE")] } }
Step2 { fuel: 15, per_tick_flow: 81, data: Schedule { agent: 1, distance: 4, target: "JJ" } }
Step2 { fuel: 15, per_tick_flow: 81, data: AdvanceTime { ticks: 3 } }
Step2 { fuel: 12, per_tick_flow: 81, data: EnableTick { activations: [(0, "HH")] } }
Step2 { fuel: 11, per_tick_flow: 81, data: Schedule { agent: 0, distance: 6, target: "BB" } }
Step2 { fuel: 11, per_tick_flow: 81, data: EnableTick { activations: [(1, "JJ")] } }
Step2 { fuel: 10, per_tick_flow: 81, data: Schedule { agent: 1, distance: 7, target: "HH" } }
Step2 { fuel: 10, per_tick_flow: 81, data: AdvanceTime { ticks: 5 } }
Step2 { fuel: 5, per_tick_flow: 81, data: EnableTick { activations: [(0, "BB")] } }
Step2 { fuel: 4, per_tick_flow: 81, data: Schedule { agent: 0, distance: 3, target: "JJ" } }
Step2 { fuel: 4, per_tick_flow: 81, data: AdvanceTime { ticks: 1 } }
Step2 { fuel: 3, per_tick_flow: 81, data: EnableTick { activations: [(1, "HH")] } }
Step2 { fuel: 2, per_tick_flow: 81, data: DoNothing }
1707
took 251.897791ms
```

Okay. That's great! Let's try it on the ~6 times larger (with factorially worse run time) input.

### Problems with memory (?)

```bash
$ cargo run --release --bin 16-pressurinator 2 data/16.txt
    
   ...
   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished release [optimized] target(s) in 37.41s
     Running `target/release/16-pressurinator 2 data/16.txt`

zsh: killed     cargo run --release --bin 16-pressurinator 2 data/16.txt
```

Yeah... that's not good. It would run for several minutes and just crash. I googled, tried `cargo clean`, tried a new browser, tried it in `debug` mode (that took longer and still crashed). On branch suggested `zld` might cause this issue, but I'm not using it. I thought perhaps a Rust bug...

```bash
$ rustc --version

rustc 1.64.0

$ rustup update

info: syncing channel updates for 'stable-aarch64-apple-darwin'
info: latest update on 2022-12-15, rust version 1.66.0 (69f9c33d7 2022-12-12)
...
info: checking for self-updates

  stable-aarch64-apple-darwin updated - rustc 1.66.0 (69f9c33d7 2022-12-12) (from rustc 1.62.1 (e092d0b6b 2022-07-16))
```

Unfortunately that didn't help. Either. So ... what's going on? 

### Improving memory usage

Well, remember how I talked about `Vector` sharing structs and saving me a bunch of memory? Well, in practice... I'm either using it wrong or don't quite understand it. 

Exhibit A:

{{< figure src="/embeds/2022/aoc16-2-ram.png" >}}

Yup. That's the program (in release mode!) using **45 GB** of RAM. I'm writing most of this on an M1 Mac Mini... with 16 GB of RAM. So most of that is in swap. It actually made it up to 60 GB of RAM before the OS killed it off. 

Great. 

So, how do we fix it? 

Well, there are two big parts of the recursive calls that I should be able to optimize:

* The `im::Vector` of `enabled` valves
* The `im::Vector` of `agents`

For the first, it's a `Vector<bool>`. I should be able to pack all of those values (even 59 of them) into a single 64-bit integer. Enter [`bitvec`](https://docs.rs/bitvec/latest/bitvec/). I've given up on not using third party crates, there are some things that (after hours and hours of working on this) I don't want to reimplement just now. 

For the conversion, we kick it off with this instead:

```rust
// Init the agents and kick the recursive function off
let cave = Rc::new(self);
let (total_flow, steps) = recur(
    cave.clone(),
    Rc::new(RefCell::new(HashMap::new())),
    Vector::from(vec![State::new(cave.clone().indexes[&location]); agents]),
    fuel,
    BitVec::from_vec(vec![0; cave.clone().size]),
);
```

Then we need to change the various cache types and function signatures to expect this value and finally change the `enabled[agent.index] = true` to `enabled.set(agent.index, true)`. After that, it just works. We're still `clone`ing it, but it's a 64-bit integer being copied. Much better. 

Next up, `agents`. This doesn't change much. Really for two, it's 4 `usize` values (an `index` and `ttl` for each). So instead of `Vector`, I just switched to `Vec`. It turns out it's optimized all to heck and cheap enough to copy those two bytes rather than all the extra bookkeeping from `Vector`. 

All of that done and...

{{< figure src="/embeds/2022/aoc16-2-better.png" >}}

It's still taking up a chunk of my machine... but it's better!

I'm ... not 100% sure what the difference between `Real Memory Size` and `Virtual Memory Size` is there. I think `Real` is what it's actually using and `Virtual` is what it theoretically has access to? In that case, we should be good to go. 

### Improving runtime

It's still very slow. So... how can we do better? Well, remember how I said that in both the `EnableTick` and `AdvanceTime` states there was only one possibility? Well branching (in this case) is expensive and takes even more memory. So let's see if we can clean everything up into a single case.

```rust
impl Cave {
    // The same simulation but with multiple agents
    fn max_flow_multi(
        self,
        location: String,
        fuel: usize,
        agents: usize,
    ) -> (usize, Vec<StepMulti>) {
        type CacheKey = (Vec<State>, usize, BitVec);
        type CacheValue = (usize, Vec<StepMulti>);

        // Main recursive function with multiple agents
        // cave and cache still don't change (other than to cache values)
        // agents is an im::Vector of agent states, can be any number (even 1)
        // - this contains the next index
        // - plus a new value ttl which is how long it will take the agent to get to the index
        // fuel is how long the simulation can still run
        // enabled is the map of which flows are enabled
        fn recur(
            cave: Rc<Cave>,
            cache: Rc<RefCell<HashMap<CacheKey, CacheValue>>>,
            agents: Vec<State>,
            fuel: usize,
            enabled: BitVec,
        ) -> CacheValue {
            // Cache based on the state of all agents/fuel/enabled
            let cache_key = (agents.clone(), fuel, enabled.clone());
            if cache.borrow().contains_key(&cache_key) {
                return cache.borrow_mut()[&cache_key].clone();
            }

            // Calculate flow per tick (even if we won't actually tick)
            let per_tick_flow = cave
                .clone()
                .flow_rates
                .iter()
                .zip(enabled.clone().iter())
                .filter_map(|(f, c)| if *c { Some(*f) } else { None })
                .sum::<usize>();

            // Base case: try doing nothing for the rest of the simulation
            let mut result = (
                fuel * per_tick_flow,
                vec![StepMulti {
                    fuel,
                    per_tick_flow,
                    data: StepMultiData::DoNothing,
                }],
            );

            // Once all useful flows are active, allow moving to anywhere
            // This fixes a previous bug where the first free agent would claim the last valve even it was further away
            let potential_enabled = cave
                .clone()
                .flow_rates
                .iter()
                .zip(enabled.clone())
                .filter_map(|(f, e)| if *f > 0 && !e { Some(true) } else { None })
                .count();

            // If the TTL of any agent is 0, schedule it's next move
            // This doesn't advance time
            if let Some((i, agent)) = agents.clone().iter().enumerate().find(|(_, a)| a.ttl == 0) {
                for next_index in 0..cave.clone().size {
                    // Not allowed to move to the same target as any other agent
                    // Can only move to an already enabled valve if we're in the end state
                    if agents.clone().iter().any(|a| next_index == a.index)
                        || (potential_enabled >= agents.len() && enabled[next_index])
                        || cave.clone().flow_rates[next_index] == 0
                    {
                        continue;
                    }

                    // Check that we have enough fuel to move there
                    let d = cave.clone().distances[[agent.index, next_index]];
                    if d + 1 > fuel {
                        continue;
                    }

                    // Update the agent with where it's going + how long to get there and enable
                    let mut new_agents = agents.clone();
                    new_agents[i] = State {
                        index: next_index,
                        ttl: d + 1,
                    };

                    // Make the recursive call and record that we did
                    let mut sub_result = recur(
                        cave.clone(),
                        cache.clone(),
                        new_agents,
                        fuel,
                        enabled.clone(),
                    );
                    sub_result.1.push(StepMulti {
                        fuel,
                        per_tick_flow,
                        data: StepMultiData::Schedule {
                            agent: i,
                            distance: d,
                            target: cave.clone().names[next_index].clone(),
                        },
                    });

                    // If making this call was better than the current result (of do nothing)
                    // Use it instead
                    result = result.max(sub_result);
                }
            }
            // Otherwise, advance by the ttl of the lowest agent
            else {
                let mut activations = Vec::new();

                // Find time until the agent(s) that will finish moving soonest
                let ticks = agents
                    .clone()
                    .iter()
                    .min_by(|a, b| a.ttl.cmp(&b.ttl))
                    .expect("must have at least one agent")
                    .ttl;

                // Enable any flows for agents with TTL=0 at the end of this move
                let mut next_enabled = enabled.clone();
                for (i, agent) in agents.clone().iter().enumerate() {
                    if agent.ttl == ticks {
                        next_enabled.set(agent.index, true);
                        activations.push((i, cave.clone().names[agent.index].clone()));
                    }
                }

                // Update all agents (including those that will go to 0)
                let mut next_agents = agents.clone();
                for (i, agent) in agents.clone().iter().enumerate() {
                    next_agents[i] = agent.tick(ticks);
                }

                // Make the recursive call
                let mut sub_result = recur(
                    cave.clone(),
                    cache.clone(),
                    next_agents,
                    fuel - ticks,
                    next_enabled,
                );

                // Update flow by that many ticks + record what step we took
                // As always, if this result is better than nothing, record it
                sub_result.0 += ticks * per_tick_flow;
                sub_result.1.push(StepMulti {
                    fuel,
                    per_tick_flow,
                    data: StepMultiData::AdvanceTime { ticks, activations },
                });
                result = result.max(sub_result);
            }

            // Memoize the result and finally return
            cache.borrow_mut().insert(cache_key, result.clone());
            result
        }

        // Init the agents and kick the recursive function off
        let cave = Rc::new(self);
        let (total_flow, steps) = recur(
            cave.clone(),
            Rc::new(RefCell::new(HashMap::new())),
            vec![State::new(cave.clone().indexes[&location]); agents],
            fuel,
            BitVec::from_vec(vec![0; cave.clone().size]),
        );

        // Because we're using Vec, the steps end up in reverse order
        (total_flow, steps.into_iter().rev().collect::<Vec<_>>())
    }
}
```

Basically I got rid of the relatively annoying `ttl = 1` state and instead handle that and the `advance` in the same tick. It's a bit cleaner code and a bit quicker. 

### To be continued...

Unfortunately, a bit quicker is still way too slow. At this point, I've been working on this problem for quite a while, so I'm going to go ahead and move on to another. I'll let it run overnight to get an answer (if it does), but I still do want to try something better. 

I think one option would be to give up on perfect and instead try a heuristic approach like {{<wikipedia "simulated annealing">}}. It won't be able to guarantee me the perfect answer, but I expect it will find one good enough in far less time. 

Like I said, to be continued...

Certainly one of the most interesting problems so far this year!

### Edit Dec 20: Let it run!

So the good news is:

```bash
cargo run --release --bin 16-pressurinator 2 data/16.txt

    Finished release [optimized] target(s) in 0.15s
     Running `target/release/16-pressurinator 2 data/16.txt`
StepMulti { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 0, distance: 2, target: "CA" } }
StepMulti { fuel: 26, per_tick_flow: 0, data: Schedule { agent: 1, distance: 2, target: "TU" } }
StepMulti { fuel: 26, per_tick_flow: 0, data: AdvanceTime { ticks: 3, activations: [(0, "CA"), (1, "TU")] } }
StepMulti { fuel: 23, per_tick_flow: 24, data: Schedule { agent: 0, distance: 3, target: "FP" } }
StepMulti { fuel: 23, per_tick_flow: 24, data: Schedule { agent: 1, distance: 2, target: "UK" } }
StepMulti { fuel: 23, per_tick_flow: 24, data: AdvanceTime { ticks: 3, activations: [(1, "UK")] } }
StepMulti { fuel: 20, per_tick_flow: 42, data: Schedule { agent: 1, distance: 3, target: "EK" } }
StepMulti { fuel: 20, per_tick_flow: 42, data: AdvanceTime { ticks: 1, activations: [(0, "FP")] } }
StepMulti { fuel: 19, per_tick_flow: 47, data: Schedule { agent: 0, distance: 2, target: "YH" } }
StepMulti { fuel: 19, per_tick_flow: 47, data: AdvanceTime { ticks: 3, activations: [(0, "YH"), (1, "EK")] } }
StepMulti { fuel: 16, per_tick_flow: 87, data: Schedule { agent: 0, distance: 2, target: "UX" } }
StepMulti { fuel: 16, per_tick_flow: 87, data: Schedule { agent: 1, distance: 3, target: "GW" } }
StepMulti { fuel: 16, per_tick_flow: 87, data: AdvanceTime { ticks: 3, activations: [(0, "UX")] } }
StepMulti { fuel: 13, per_tick_flow: 110, data: Schedule { agent: 0, distance: 2, target: "AR" } }
StepMulti { fuel: 13, per_tick_flow: 110, data: AdvanceTime { ticks: 1, activations: [(1, "GW")] } }
StepMulti { fuel: 12, per_tick_flow: 126, data: Schedule { agent: 1, distance: 2, target: "JT" } }
StepMulti { fuel: 12, per_tick_flow: 126, data: AdvanceTime { ticks: 2, activations: [(0, "AR")] } }
StepMulti { fuel: 10, per_tick_flow: 146, data: Schedule { agent: 0, distance: 8, target: "JF" } }
StepMulti { fuel: 10, per_tick_flow: 146, data: AdvanceTime { ticks: 1, activations: [(1, "JT")] } }
StepMulti { fuel: 9, per_tick_flow: 168, data: DoNothing }
2536
took 9366.7117265s
```

2.5 hours, but it finished!

The bad news is... that's apparently not actually my answer. But apparently:

> That's not the right answer; your answer is too low. Curiously, it's the right answer for someone else; you might be logged in to the wrong account or just unlucky.

That's kind of hilarious. 

Back to the drawing board!

<!-- ## Performance -->
