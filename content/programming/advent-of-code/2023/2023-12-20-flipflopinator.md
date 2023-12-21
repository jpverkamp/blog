---
title: "AoC 2023 Day 20: Flip-Flopinator"
date: 2023-12-20 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 20: Pulse Propagation](https://adventofcode.com/2023/day/20)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day20) for today (spoilers!)

{{<toc>}}

## Part 1

> Simulate a virtual circuit with `high` and `low` pulses and four kinds of chips:
>
> * Broadcast - Re-transmit all pulses 
> * Flip-flops - On a `low` pulse, toggle internal state; if it was on, send `high`; otherwise send `low`
> * Conjunction - Remember input from each attached module; if all inputs were `high`, send a `low`, otherwise send `high`
> * Output - Do nothing; just receive pulses
>
> Count the product of `low` and `high` pulses sent after 1000 `low` inputs to `broadcaster`.

<!--more-->

### Types and Parsing

Our types are a bit more interesting than often this time:

```rust
use fxhash::FxHashMap;

#[derive(Debug, Clone)]
pub enum ModuleType<'a> {
    Broadcast,
    FlipFlop(bool),
    Conjunction(FxHashMap<&'a str, Pulse>),
    Output,
}

#[derive(Debug, Clone)]
pub struct Module<'a> {
    pub label: &'a str,
    pub module_type: ModuleType<'a>,
    pub outputs: Vec<&'a str>,
}

#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum Pulse {
    High,
    Low,
}
```

Specifically, the `ModuleType::FlipFlop` stores if was previously on and the `Conjunction` stores a map of input labels to what the last `Pulse` it received from each. 

Now for parsing:

```rust
fn module_type(input: &str) -> IResult<&str, ModuleType> {
    alt((
        map(complete::char('%'), |_| ModuleType::FlipFlop(false)),
        map(complete::char('&'), |_| {
            ModuleType::Conjunction(FxHashMap::default())
        }),
    ))(input)
}

fn broadcast_module(input: &str) -> IResult<&str, (ModuleType, &str)> {
    let (input, name) = tag("broadcaster")(input)?;
    Ok((input, (ModuleType::Broadcast, name)))
}

fn other_module(input: &str) -> IResult<&str, (ModuleType, &str)> {
    pair(module_type, alpha1)(input)
}

fn module(input: &str) -> IResult<&str, Module> {
    let (input, (module_type, label)) = alt((broadcast_module, other_module))(input)?;
    let (input, _) = delimited(space0, tag("->"), space0)(input)?;
    let (input, outputs) = separated_list1(terminated(complete::char(','), space0), alpha1)(input)?;

    Ok((
        input,
        Module {
            label,
            module_type,
            outputs,
        },
    ))
}

pub fn modules(input: &str) -> IResult<&str, FxHashMap<&str, Module>> {
    let (input, modules) = separated_list1(line_ending, module)(input)?;

    let mut modules = modules
        .iter()
        .map(|module| (module.label, module.clone()))
        .collect::<FxHashMap<_, _>>();

    let inputs = modules
        .iter()
        .flat_map(|(label, module)| module.outputs.iter().map(|output| (*output, *label)))
        .collect::<Vec<_>>();

    for (output, label) in inputs {
        if let Some(module) = modules.get_mut(output) {
            // Conjunctions need a reference back to their inputs
            match module.module_type {
                ModuleType::Conjunction(ref mut inputs) => {
                    inputs.insert(label, Pulse::Low);
                }
                _ => {}
            }
        } else {
            // If the output doesn't exist, create it as an output module
            modules.insert(
                output,
                Module {
                    label: output,
                    module_type: ModuleType::Output,
                    outputs: vec![],
                },
            );
        }
    }

    Ok((input, modules))
}
```

There are a couple interesting bits here:

* Because `broadcaster` modules don't have a prefix, we parse it as an `alt` in `module`
* `modules` goes through a few steps:
  * Parse the modules
  * Collect the `inputs` by inverting the `module::output` lists
  * Initialize the `FxHashMap` of previous values for `ModuleType::Conjunctions` with the `inputs`

### Solution

Okay, let's do it!

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, mut modules) = parse::modules(&input).unwrap();
    assert_eq!(s.trim(), "");

    let mut state = modules
        .keys()
        .map(|label| (*label, Pulse::Low))
        .collect::<FxHashMap<_, _>>();

    let mut low_sent = 0;
    let mut high_sent = 0;

    for push_i in 1..=1000 {
        log::info!("=== Push {push_i} ===");
        let mut queue = VecDeque::from(vec![("button", "broadcaster", Pulse::Low)]);

        while let Some((src, dst, pulse)) = queue.pop_front() {
            log::info!("{src} -{pulse:?}-> {dst}");

            match pulse {
                Pulse::Low => low_sent += 1,
                Pulse::High => high_sent += 1,
            }

            let module = modules.get_mut(dst).unwrap();
            state.insert(dst, pulse);

            match module.module_type {
                // Broadcast modules send the received pulse to all outputs
                ModuleType::Broadcast => {
                    for output in &module.outputs {
                        queue.push_back((dst, *output, pulse));
                    }
                }
                // Flip-flops flip on low pulses
                // If it was off, it turns on and sends high
                // If it was on, it turns off and sends low
                ModuleType::FlipFlop(ref mut is_on) => {
                    if pulse == Pulse::Low {
                        let output_pulse = if *is_on { Pulse::Low } else { Pulse::High };
                        for output in &module.outputs {
                            queue.push_back((dst, *output, output_pulse));
                        }

                        *is_on = !*is_on;
                    }
                }
                // Conjunctions remember previous inputs
                // If all inputs are high, sends a low
                // Otherwise, send a high
                ModuleType::Conjunction(ref mut inputs) => {
                    inputs.insert(src, pulse);

                    let output_pulse = if inputs.values().all(|pulse| *pulse == Pulse::High) {
                        Pulse::Low
                    } else {
                        Pulse::High
                    };

                    for output in &module.outputs {
                        queue.push_back((dst, *output, output_pulse));
                    }
                }
                // Output modules do nothing
                ModuleType::Output => {}
            }
        }
    }

    log::info!(" low_sent: {low_sent}");
    log::info!("high_sent: {high_sent}");

    let result = low_sent * high_sent;

    println!("{result}");
    Ok(())
}
```

Each tick waits for the entire simulation to 'settle' before moving on, so we'll keep a new `queue` within each iteration. Fire off the `broadcaster` and away we go!

I like how storing the extra data (on/off for flip flops and inputs for conjunctions) is the `ModuleType` works here. The `match` gets the data it needs, but you don't have extra metadata that you aren't actually using. `enums` with data for the win!

## Part 2

> How many button presses / cycles does it take for `rx` to send a `low` pulse? 

### Solution 1: Brute Force

Well, worth trying it, no? 

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, mut modules) = parse::modules(&input).unwrap();
    assert_eq!(s.trim(), "");

    let mut state = modules
        .keys()
        .map(|label| (*label, Pulse::Low))
        .collect::<FxHashMap<_, _>>();

    let mut push_i = 0;
    'simulation: loop {
        push_i += 1;
        
        let mut queue = VecDeque::from(vec![("button", "broadcaster", Pulse::Low)]);

        while let Some((src, dst, pulse)) = queue.pop_front() {
            log::info!("{src} -{pulse:?}-> {dst}");

            if dst == "rx" && pulse == Pulse::Low {
                break 'simulation;
            }

            // ...
        }
    }

    log::info!("   pushes: {push_i}");

    let result = push_i;

    println!("{result}");
    Ok(())
}
```

And ... away it goes. 

And ... for hours doesn't actually return anything. 

I expect we're specifically set up with something that's going to take *ages* to simulate again. That seems to be the way things go this year. :smile:

### A pretty picture

Okay, things are taking *entirely* too long. Let's visualize what we're actually doing here. 

A quick script to generate [GraphViz](https://graphviz.org/) [Dot](https://graphviz.org/doc/info/lang.html) files:

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, modules) = parse::modules(&input).unwrap();
    assert_eq!(s.trim(), "");

    println!("digraph G {{");

    // Nodes with labels
    modules
        .iter()
        .for_each(|(label, module)| println!("{}", match module.module_type {
            ModuleType::Broadcast => format!("  {label}"),
            ModuleType::FlipFlop(_) => format!("  {label} [label=\"%{label}\", color=\"blue\"];"),
            ModuleType::Conjunction(_) => format!("  {label} [label=\"&{label}\", color=\"green\"];"),
            ModuleType::Output => format!("  {label}"),
        }));

    // Edges
    modules.iter().for_each(|(label, module)| {
        module
            .outputs
            .iter()
            .for_each(|output| println!("  {} -> {};", label, output));
    });

    println!("}}");

    Ok(())
}
```

And we have:

{{<figure src="/embeds/2023/aoc23-20.svg">}}

That's actually pretty interesting. I'd rather drag it around a bit, but if you look carefully, it appears that `rx` depends *entirely* on the conjunction `gq`. Which in turn, requires that exactly four conjunctions are set: `mf`, `xj`, `km`, and `kz`. Going back further, each of those appears to be completely independent--there aren't connections between the nodes all the way back until the `broadcast` node. 

Reaching a bit, my bet is that each of those four nodes is actually a very slow generator, it will generate a single pulse ever `x` ticks. And then much like [[AoC 2023 Day 8: Mazinator|day 8]]()... those cycles will align based on their [[wiki:least common multiple]](). 

Let's try it.

### Solution 2: Least common multiple

We have the node names for our specific puzzle, but let's generalize a bit. Still assume that there's a single collection node and then 4 before that, but we can collect those:

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, mut modules) = parse::modules(&input).unwrap();
    assert_eq!(s.trim(), "");

    let mut state = modules
        .keys()
        .map(|label| (*label, Pulse::Low))
        .collect::<FxHashMap<_, _>>();

    // rx comes from exactly one node
    let targets = modules
        .iter()
        .filter(|(_, module)| module.outputs.iter().any(|output| *output == "rx"))
        .map(|(label, _)| *label)
        .collect::<Vec<_>>();

    // That node in turn comes from 4 that each turn on every so many frames
    let mut targets = modules
        .iter()
        .filter(|(_, module)| module.outputs.iter().any(|output| targets.iter().any(|target| target == output)))
        .map(|(label, _)| *label)
        .collect::<Vec<_>>();

    // Collect the lengths of those cycles
    let mut cycles = Vec::new();

    let mut push_i = 0;
    'simulation: loop {
        push_i += 1;
        log::info!("=== Push {push_i} ===");
        
        let mut queue = VecDeque::from(vec![("button", "broadcaster", Pulse::Low)]);

        while let Some((src, dst, pulse)) = queue.pop_front() {
            log::info!("{src} -{pulse:?}-> {dst}");

            if let Some(i) = targets.iter().position(|node| *node == dst) {
                if pulse == Pulse::Low {
                    targets.remove(i);
                    cycles.push(push_i as usize);
                }
            }

            if targets.is_empty() {
                break 'simulation;
            }

            let module = modules.get_mut(dst).unwrap();
            state.insert(dst, pulse);

            match module.module_type {
                // Broadcast modules send the received pulse to all outputs
                ModuleType::Broadcast => {
                    for output in &module.outputs {
                        queue.push_back((dst, *output, pulse));
                    }
                }
                // Flip-flops flip on low pulses
                // If it was off, it turns on and sends high
                // If it was on, it turns off and sends low
                ModuleType::FlipFlop(ref mut is_on) => {
                    if pulse == Pulse::Low {
                        let output_pulse = if *is_on { Pulse::Low } else { Pulse::High };
                        for output in &module.outputs {
                            queue.push_back((dst, *output, output_pulse));
                        }

                        *is_on = !*is_on;
                    }
                }
                // Conjunctions remember previous inputs
                // If all inputs are high, sends a low
                // Otherwise, send a high
                ModuleType::Conjunction(ref mut inputs) => {
                    inputs.insert(src, pulse);

                    let output_pulse = if inputs.values().all(|pulse| *pulse == Pulse::High) {
                        Pulse::Low
                    } else {
                        Pulse::High
                    };

                    for output in &module.outputs {
                        queue.push_back((dst, *output, output_pulse));
                    }
                }
                // Output modules do nothing
                ModuleType::Output => {}
            }
        }
    }

    log::info!("cycles: {cycles:?}");

    fn gcd(a: usize, b: usize) -> usize {
        if b == 0 {
            a
        } else {
            gcd(b, a % b)
        }
    }

    fn lcm(a: usize, b: usize) -> usize {
        a / gcd(a, b) * b
    }
    
    let result = cycles.into_iter().reduce(lcm).unwrap();

    println!("{result}");
    Ok(())
}
```

So `targets` the first time is `gq` and the second (final) time it will be `mf`, `xj`, `km`, and `kz`. For each of those, figure out when they fire, then apply the `lcm`. 

And ... it works!

I think there probably could have been some setup to this one (off by 1 errors), but it turned out to be the right answer so I just went with it. 

Much like [[AoC 2023 Day 8: Mazinator|day 8]](), it feels a bit magic, but at least this time I generated the image and looked at it, so the fact that there are four cycles that have to line up makes sense to me!

And yes. The answer is ~240 trillion. So again, a *long* time to simulate. 

## Performance

```bash
$ just time 20 1

hyperfine --warmup 3 'just run 20 1'
Benchmark 1: just run 20 1
  Time (mean ± σ):     212.6 ms ±  75.9 ms    [User: 48.2 ms, System: 19.8 ms]
  Range (min … max):   125.3 ms … 350.1 ms    22 runs

$ just time 20 2

hyperfine --warmup 3 'just run 20 2'
Benchmark 1: just run 20 2
  Time (mean ± σ):     371.3 ms ± 174.5 ms    [User: 67.9 ms, System: 20.0 ms]
  Range (min … max):   146.1 ms … 616.9 ms    10 runs
```

Well, it's much better than days/months/years for the brute force solution, but I feel like we could do better. Perhaps a direct conversion of the gates? 

Another time. 