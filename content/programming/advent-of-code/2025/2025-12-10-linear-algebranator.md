---
title: "AoC 2025 Day 10: Linear Algebranator"
date: 2025-12-10 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics:
- BFS
- Branch and Bound
- Memoization
- Z3
- Integer Linear Programming
- SMT Solver
- Optimization
- Combinatorics
- Parallelism
- Rayon
---
## Source: [Day 10: Factory](https://adventofcode.com/2025/day/10)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day10.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a target light pattern `[.##.]` and a series of buttons (`(3) (1, 3) etc`) where the first button toggles light '3' (the 4th light) and the second toggles the first and 4th etc, what is the minimum number of buttons you need to press to match the light pattern. 

<!--more-->

Okay, first: parsing.

```rust
#[derive(Debug)]
struct Machine {
    // Cache the size of machine
    size: usize,
    // The target states of lights, true means light should be turned on
    lights: Vec<bool>,
    // Sets of buttons, each button toggles the given index of wires
    // So if buttons[0] is [3, 4, 5], button 0 will toggle 3, 4, and 5
    buttons: Vec<Vec<usize>>,
    // Target joltage requirements
    joltage: Vec<usize>,
}

impl From<&str> for Machine {
    fn from(value: &str) -> Self {
        let parts = value.split_ascii_whitespace().collect::<Vec<_>>();

        let light_part = parts[0];
        let lights = light_part[1..light_part.len() - 1]
            .chars()
            .map(|c| c == '#')
            .collect::<Vec<_>>();

        let size = lights.len();

        let button_parts = &parts[1..parts.len() - 1];
        let buttons = button_parts
            .iter()
            .map(|button| {
                button[1..button.len() - 1]
                    .split(',')
                    .map(|v| v.parse::<usize>().unwrap())
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>();

        let joltage_part = parts[parts.len() - 1];
        let joltage = joltage_part[1..joltage_part.len() - 1]
            .split(',')
            .map(|v| v.parse::<usize>().unwrap())
            .collect::<Vec<_>>();

        Self {
            size,
            lights,
            buttons,
            joltage,
        }
    }
}
```

> Because none of the machines are running, the joltage requirements are irrelevant and can be safely ignored.

Uh huh. 

So this is actually a fairly straight forward [[wiki:depth-first search]]():

```rust
impl Machine {
    fn solve_lights(&self) -> usize {
        let mut queue = VecDeque::new();
        queue.push_back((0, vec![false; self.size]));

        while let Some((presses, lights)) = queue.pop_front() {
            for button in self.buttons.iter() {
                let new_lights = lights
                    .iter()
                    .enumerate()
                    .map(|(i, on)| if button.contains(&i) { !on } else { *on })
                    .collect::<Vec<_>>();

                queue.push_back((presses + 1, new_lights));
            }
        }

        unreachable!("no solution found");
    }
}
```

Start with `0` presses and no lights on, keep scanning until we found the pattern:

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .map(|m| m.solve_lights())
        .sum::<usize>()
        .to_string()
}
```

One trick I went ahead and did here (pulling in the {{<crate rayon>}} crate *gasp*), was to auto-parallelize it:

```rust
#[aoc::register]
fn part1_rayon(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .par_bridge()
        .map(|m| m.solve_lights())
        .sum::<usize>()
        .to_string()
}
```

So how does it run? 

```bash
$ just run-and-bench 10 part1 10

452

part1: 1.212226433s ± 13.832532ms [min: 1.199442042s, max: 1.247776833s, median: 1.208264834s]

$ just run-and-bench 10 part1_rayon 10

452

part1_rayon: 331.882295ms ± 5.14392ms [min: 324.905666ms, max: 342.0265ms, median: 331.103208ms]
```

I ... am not thrilled with this. 

And feel like part 2 is going to be fun(tm). 

## Part 2

> Instead of lights, you have to hit the target joltages. So `(3)` increases the 4th `joltage` by 1 and `(1 3)` increments the 2nd and 4th. What is the minimum number of button presses to hit the target joltages. 

So it's the same program, just much bigger, right? 

```rust
impl Machine {
    fn solve_joltage(&self) -> usize {
        log::info!("Working on {self:?}");

        let mut queue = VecDeque::new();
        queue.push_back((0, vec![0; self.size]));

        while let Some((presses, joltages)) = queue.pop_front() {
            log::debug!("[{presses}, {}] {joltages:?}", queue.len());

            if joltages == self.joltage {
                log::info!("Found solution {presses}");
                return presses;
            }

            if joltages
                .iter()
                .zip(self.joltage.iter())
                .any(|(current, target)| current > target)
            {
                log::debug!("OVER JOLTAGE!");
                continue;
            }

            for button in self.buttons.iter() {
                let new_joltages = joltages
                    .iter()
                    .enumerate()
                    .map(|(i, v)| if button.contains(&i) { v + 1 } else { *v })
                    .collect::<Vec<_>>();

                queue.push_back((presses + 1, new_joltages));
            }
        }

        unreachable!("no solution found");
    }
}

#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .map(|m| m.solve_joltage())
        .sum::<usize>()
        .to_string()
}

#[aoc::register]
fn part2_rayon(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .par_bridge()
        .map(|m| m.solve_joltage())
        .sum::<usize>()
        .to_string()
}
```

Yeah... that's never going to finish. 

## Part 2 - A system of equations [WIP]

Here's a partial solution. The idea was that we have a system of equations. If we add and subtract a bunch of them, can we find any of the numbers that way? 

```rust
impl Equation {
    fn negated(&self) -> Self {
        Equation {
            constant: -self.constant,
            coefficients: self.coefficients.iter().map(|&c| -c).collect::<Vec<_>>(),
        }
    }

    fn reduced(&self) -> Self {
        let gcd = self
            .coefficients
            .iter()
            .cloned()
            .filter(|&c| c != 0)
            .fold(0, num::integer::gcd);
        let reduced = if gcd == 0 || gcd == 1 {
            self.clone()
        } else {
            Equation {
                constant: self.constant / gcd,
                coefficients: self
                    .coefficients
                    .iter()
                    .map(|&c| c / gcd)
                    .collect::<Vec<_>>(),
            }
        };

        if reduced.constant < 0 {
            reduced.negated()
        } else {
            reduced
        }
    }
}

impl std::fmt::Display for Equation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let terms: Vec<String> = self
            .coefficients
            .iter()
            .enumerate()
            .filter(|(_, coef)| **coef != 0)
            .map(|(i, &coef)| format!("{coef} * x{i}"))
            .collect();
        write!(f, "{} = {}", terms.join(" + "), self.constant)
    }
}

impl Machine {
    fn solve_joltage_eqn(&self) -> usize {
        log::info!("Working on {self:?}");

        let mut equations: HashSet<Equation> = HashSet::new();
        for idx in 0..self.size {
            let mut coefficients = vec![0; self.buttons.len()];
            for (bi, button) in self.buttons.iter().enumerate() {
                if button.contains(&idx) {
                    coefficients[bi] = 1;
                }
            }
            equations.insert(Equation {
                constant: self.joltage[idx] as isize,
                coefficients,
            });
        }

        for eq in &equations {
            log::info!("Equation: {eq}");
        }

        let mut known_values = vec![None; self.buttons.len()];

        for _i in 0.. {
            if _i >= 3 {
                break; // DEBUG
            }
            println!("Expanding equations, iter={_i}, count={}", equations.len());

            let initial_equations = equations.clone();
            let initial_size = equations.len();

            for eq1 in initial_equations.iter() {
                for eq2 in initial_equations.iter() {
                    if eq1 != eq2 {
                        equations.insert(eq1.clone() + eq2.clone());
                        equations.insert(eq1.clone().negated() + eq2.clone());
                        equations.insert(eq2.clone().negated() + eq1.clone());
                    }
                }
            }
            if equations.len() == initial_size {
                break;
            }

            // Look for any single-variable equations
            let single_var_eqs: Vec<Equation> = equations
                .iter()
                .filter(|eq| eq.coefficients.iter().filter(|&&c| c != 0).count() == 1)
                .cloned()
                .collect();

            println!("Found {} single-variable equations", single_var_eqs.len());
            for eq in single_var_eqs.iter() {
                println!("  {eq}");
            }

            // Record known values
            for eq in single_var_eqs.iter() {
                let xi = eq
                    .coefficients
                    .iter()
                    .position(|&c| c != 0)
                    .unwrap();

                known_values[xi] = Some(eq.constant as usize);
            }
            println!("Known values so far: {:?}", known_values);


            // Remove all equations that use only known values
            equations = equations
                .into_iter()
                .filter(|eq| {
                    eq.coefficients
                        .iter()
                        .enumerate()
                        .any(|(i, &c)| c != 0 && known_values[i].is_none())
                })
                .collect();

            // Look for any equations with exactly two values and constant = 0
            let two_var_zero_eqs: Vec<Equation> = equations
                .iter()
                .filter(|eq| eq.coefficients.iter().filter(|&&c| c != 0).count() == 2)
                .cloned()
                .collect();

            println!("Found {} two-variable", two_var_zero_eqs.len());
            for eq in two_var_zero_eqs {
                println!("  {eq}");
            }
        }

        panic!()
    }
}
```

And running it:

```bash
$ head -n 1 input/2025/day10.txt | RUST_LOG=debug cargo run --release --bin day10 run part2_eqn -

    Finished `release` profile [optimized] target(s) in 0.05s
     Running `target/release/day10 run part2_eqn -`
[2025-12-11T05:27:20Z INFO  day10] Working on Machine { size: 8, lights: [false, true, true, true, false, true, false, false], buttons: [[0, 2, 3, 4, 6, 7], [1, 2, 4, 5, 6], [1, 3, 4, 5, 7], [0, 2, 4], [4, 7], [0, 1, 4, 6], [1, 2, 3, 4, 5, 7], [2, 4, 7]], joltage: [29, 44, 42, 26, 66, 27, 30, 36] }
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x1 + 1 * x3 + 1 * x6 + 1 * x7 = 42
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x1 + 1 * x2 + 1 * x3 + 1 * x4 + 1 * x5 + 1 * x6 + 1 * x7 = 66
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x2 + 1 * x4 + 1 * x6 + 1 * x7 = 36
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x3 + 1 * x5 = 29
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x1 + 1 * x2 + 1 * x5 + 1 * x6 = 44
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x2 + 1 * x6 = 26
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x1 + 1 * x2 + 1 * x6 = 27
[2025-12-11T05:27:20Z INFO  day10] Equation: 1 * x0 + 1 * x1 + 1 * x5 = 30
Expanding equations, iter=0, count=8
Found 1 single-variable equations
  1 * x5 = 17
Known values so far: [None, None, None, None, None, Some(17), None, None]
Found 3 two-variable
  1 * x4 + 1 * x7 = 10
  -1 * x0 + 1 * x1 = 1
  1 * x1 + -1 * x3 = 1
Expanding equations, iter=1, count=63
Found 2 single-variable equations
  1 * x0 = 6
  1 * x5 = 17
Known values so far: [Some(6), None, None, None, None, Some(17), None, None]
Found 13 two-variable
  -1 * x0 + 1 * x3 = 0
  1 * x1 + 1 * x3 = 13
  1 * x1 + 1 * x5 = 24
  1 * x2 + 1 * x4 = 7
  1 * x0 + 1 * x3 = 12
  1 * x0 + -1 * x3 = 0
  1 * x0 + 1 * x1 = 13
  -1 * x0 + 1 * x1 = 1
  1 * x1 + -1 * x3 = 1
  2 * x3 + 1 * x5 = 29
  1 * x2 + 1 * x6 = 20
  1 * x4 + 1 * x7 = 10
  2 * x1 + 1 * x5 = 31
Expanding equations, iter=2, count=1481
Found 4 single-variable equations
  1 * x5 = 17
  1 * x3 = 6
  1 * x1 = 7
  1 * x0 = 6
Known values so far: [Some(6), Some(7), None, Some(6), None, Some(17), None, None]
Found 5 two-variable
  -1 * x2 + 1 * x7 = 3
  1 * x2 + 1 * x4 = 7
  1 * x2 + 1 * x6 = 20
  -1 * x4 + 1 * x6 = 13
  1 * x4 + 1 * x7 = 10

thread 'main' panicked at src/bin/day10.rs:449:9:
explicit panic
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
;_; code=101
```

There's something there. Just by shoving equations around, we know:

```text
x0 = 6
x1 = 7
x3 = 6
x5 = 17
```

And what's more, we have 5 equations that directly relate two variables, for example, we know:

```text
x2 + x4 = 7
x2 + x6 = 20
```

I might have to come back to this one.

## Part 2 - Memoization

Okay, let's go back to the original solution and apply another couple of tricks. 

First: [[wiki:memoization]](). Solve the problem recursively and every time we find the answer to a smaller part of the problem, write that down. Then build up increasingly large 'memoized' answers until we have it all. 

Second: Let's recur relatively intelligently. We know that there are a few joltage values that are only controller by a very few buttons. Let's solve those first, since they have the highest 'branching factor' (in theory). 

```rust
impl Machine {
    fn solve_joltage_memo(&self) -> usize {
        log::info!("Working on {self:?}");

        let mut memo = std::collections::HashMap::new();
        let mut stats = (0usize, 0usize); // (hits, misses)

        fn helper(
            machine: &Machine,
            current: Vec<usize>,
            memo: &mut std::collections::HashMap<Vec<usize>, usize>,
            stats: &mut (usize, usize),
        ) -> usize {
            if let Some(&result) = memo.get(&current) {
                stats.0 += 1;
                return result;
            } else {
                stats.1 += 1;
            }

            if current == machine.joltage {
                return 0;
            }

            let mut min_presses = usize::MAX;

            // Find the joltage that is impacted by the fewest buttons taking into account current state
            // Break ties by highest remaining joltage
            let mut best_joltage_idx = None;
            let mut best_button_count = usize::MAX;
            let mut best_remaining_joltage = 0usize;
            for idx in 0..machine.size {
                // Skip any joltages that are already at target
                if current[idx] >= machine.joltage[idx] {
                    continue;
                }

                // Count how many buttons contribute to this joltage
                let button_count = machine
                    .buttons
                    .iter()
                    .filter(|button| button.contains(&idx))
                    .count();

                let remaining_joltage = machine.joltage[idx] - current[idx];
                if button_count < best_button_count
                    || (button_count == best_button_count
                        && remaining_joltage > best_remaining_joltage)
                {
                    best_button_count = button_count;
                    best_remaining_joltage = remaining_joltage;
                    best_joltage_idx = Some(idx);
                }
            }

            // Try pressing each button that affects that joltage only
            // This is still guaranteed to eventually find an optimal solution since all joltages must jolt
            for button in machine.buttons.iter() {
                if let Some(joltage_idx) = best_joltage_idx
                    && !button.contains(&joltage_idx)
                {
                    continue;
                }

                let new_joltages = current
                    .iter()
                    .enumerate()
                    .map(|(i, v)| if button.contains(&i) { v + 1 } else { *v })
                    .collect::<Vec<_>>();

                // Don't recur into cases that put any joltage over joltage
                if new_joltages
                    .iter()
                    .zip(machine.joltage.iter())
                    .any(|(current, target)| current > target)
                {
                    continue;
                }

                let recur_presses = helper(machine, new_joltages, memo, stats);
                if recur_presses != usize::MAX {
                    min_presses = min_presses.min(recur_presses + 1);
                }
            }

            memo.insert(current.clone(), min_presses);
            min_presses
        }

        let result = helper(self, vec![0; self.size], &mut memo, &mut stats);
        log::info!("Found solution: {result}");
        log::info!("Memo stats: hits={}, misses={}", stats.0, stats.1);
        result
    }
}

#[aoc::register]
fn part2_memo(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .map(|m| m.solve_joltage_memo())
        .sum::<usize>()
        .to_string()
}

#[aoc::register]
fn part2_memo_rayon(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .par_bridge()
        .map(|m| m.solve_joltage_memo())
        .sum::<usize>()
        .to_string()
}
```

So... how does it do?

```bash
$ head -n 1 input/2025/day10.txt | time RUST_LOG=debug cargo run --release --bin day10 run part2_memo -

    Finished `release` profile [optimized] target(s) in 0.05s
     Running `target/release/day10 run part2_memo -`
[2025-12-11T05:30:58Z INFO  day10] Working on Machine { size: 8, lights: [false, true, true, true, false, true, false, false], buttons: [[0, 2, 3, 4, 6, 7], [1, 2, 4, 5, 6], [1, 3, 4, 5, 7], [0, 2, 4], [4, 7], [0, 1, 4, 6], [1, 2, 3, 4, 5, 7], [2, 4, 7]], joltage: [29, 44, 42, 26, 66, 27, 30, 36] }
[2025-12-11T05:30:58Z INFO  day10] Found solution: 66
[2025-12-11T05:30:58Z INFO  day10] Memo stats: hits=462347, misses=258517
66
RUST_LOG=debug cargo run --release --bin day10 run part2_memo -  0.20s user 0.04s system 95% cpu 0.249 total
```

You know... that isn't actually all that bad? 

Unfortunately, it varies wildly when it comes to different problems:

```bash
~/Projects/advent-of-code/2025 jp@venus {git master}
$ head -n 2 input/2025/day10.txt | tail -n 1 | time RUST_LOG=debug cargo run --release --bin day10 run part2_memo -

    Finished `release` profile [optimized] target(s) in 0.05s
     Running `target/release/day10 run part2_memo -`
[2025-12-11T05:31:57Z INFO  day10] Working on Machine { size: 8, lights: [true, true, true, false, true, false, false, false], buttons: [[3, 4, 6], [1, 2, 3, 4, 5, 7], [0, 1, 2, 4], [0, 1, 3, 5, 7], [0, 1, 4, 5, 6, 7], [0, 2, 7], [4, 6], [7], [0, 6], [1, 4, 5, 6, 7]], joltage: [214, 221, 33, 36, 226, 204, 203, 217] }

...
```

(It didn't finish even several minutes later, so I gave up.)

## Part 2 - Add branch and bound

So [[wiki:branch and bound]](). 

```rust
impl Machine {
    fn solve_joltage_branch_and_bound(&self) -> usize {
        log::info!("Working on {self:?}");
        let start = std::time::Instant::now();

        let mut best_solution = usize::MAX;
        let mut memo = std::collections::HashMap::new();
        let mut stats = (0usize, 0usize); // (hits, misses)

        fn branch_and_bound_recursive(
            machine: &Machine,
            presses: usize,
            joltages: Vec<usize>,
            best_solution: &mut usize,
            memo: &mut std::collections::HashMap<Vec<usize>, Option<usize>>,
            stats: &mut (usize, usize),
        ) {
            // Check memoization first
            if let Some(cached) = memo.get(&joltages) {
                stats.0 += 1;
                match cached {
                    Some(min_remaining) => {
                        let total = presses + min_remaining;
                        if total < *best_solution {
                            *best_solution = total;
                        }
                    }
                    None => {
                        // State is infeasible
                    }
                }
                return;
            }
            stats.1 += 1;

            // Pruning: if current presses >= best known solution, stop
            if presses >= *best_solution {
                memo.insert(joltages, None);
                return;
            }

            // Check if we've found a solution
            if joltages == machine.joltage {
                *best_solution = (*best_solution).min(presses);
                memo.insert(joltages, Some(0));
                return;
            }

            // Check if we've exceeded the target (infeasible)
            if joltages
                .iter()
                .zip(machine.joltage.iter())
                .any(|(current, target)| current > target)
            {
                memo.insert(joltages, None);
                return;
            }

            // Estimate lower bound for remaining presses
            let remaining = machine
                .joltage
                .iter()
                .zip(joltages.iter())
                .map(|(target, current)| target.saturating_sub(*current))
                .max()
                .unwrap_or(0);

            // Pruning: if lower bound + current presses >= best solution, stop
            if presses + remaining >= *best_solution {
                memo.insert(joltages, None);
                return;
            }

            // Find the joltage with fewest buttons affecting it (and still needs to reach target)
            // This optimization significantly reduces the search space
            let mut best_joltage_idx = None;
            let mut best_button_count = usize::MAX;
            let mut best_remaining_joltage = 0usize;

            for idx in 0..machine.size {
                // Skip any joltages that are already at target
                if joltages[idx] >= machine.joltage[idx] {
                    continue;
                }

                // Count how many buttons contribute to this joltage
                let button_count = machine
                    .buttons
                    .iter()
                    .filter(|button| button.contains(&idx))
                    .count();

                let remaining_joltage = machine.joltage[idx] - joltages[idx];
                if button_count < best_button_count
                    || (button_count == best_button_count
                        && remaining_joltage > best_remaining_joltage)
                {
                    best_button_count = button_count;
                    best_remaining_joltage = remaining_joltage;
                    best_joltage_idx = Some(idx);
                }
            }

            let mut min_remaining_presses = usize::MAX;

            // Try pressing each button that affects the chosen joltage
            // This constrains the search to only promising branches
            for button in machine.buttons.iter() {
                if let Some(joltage_idx) = best_joltage_idx
                    && !button.contains(&joltage_idx)
                {
                    continue;
                }

                let new_joltages = joltages
                    .iter()
                    .enumerate()
                    .map(|(i, v)| if button.contains(&i) { v + 1 } else { *v })
                    .collect::<Vec<_>>();

                let initial_best = *best_solution;
                branch_and_bound_recursive(
                    machine,
                    presses + 1,
                    new_joltages,
                    best_solution,
                    memo,
                    stats,
                );

                // Track minimum remaining presses from this state
                if *best_solution != initial_best {
                    min_remaining_presses = min_remaining_presses.min(*best_solution - presses - 1);
                }
            }

            // Memoize the minimum remaining presses from this state
            if min_remaining_presses != usize::MAX {
                memo.insert(joltages, Some(min_remaining_presses));
            } else {
                memo.insert(joltages, None);
            }
        }

        branch_and_bound_recursive(
            self,
            0,
            vec![0; self.size],
            &mut best_solution,
            &mut memo,
            &mut stats,
        );

        log::info!("Found solution: {best_solution}");
        log::info!("Memo stats: hits={}, misses={}", stats.0, stats.1);
        log::info!("Elapsed time: {:.2?}", start.elapsed());

        if best_solution == usize::MAX {
            unreachable!("no solution found");
        }
        best_solution
    }
}

#[aoc::register]
fn part2_branch_and_bound(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .map(|m| m.solve_joltage_branch_and_bound())
        .sum::<usize>()
        .to_string()
}

#[aoc::register]
fn part2_branch_and_bound_rayon(input: &str) -> impl Into<String> {
    let count = input.lines().count();
    let finished = Arc::new(Mutex::new(0));
    let start = std::time::Instant::now();

    input
        .lines()
        .map(Machine::from)
        .par_bridge()
        .map(|m| {
            let result = m.solve_joltage_branch_and_bound();

            let mut finished = finished.lock().unwrap();
            *finished += 1;

            log::info!(
                "Completed {}/{} machines after {:.2?}",
                *finished,
                count,
                start.elapsed()
            );

            result
        })
        .sum::<usize>()
        .to_string()
}
```

That's getting to be an awful lot of code. 

This one is the most successful I've had so far though. 

```bash
~/Projects/advent-of-code/2025 jp@venus {git master}
$ RUST_LOG=info just run 10 part2_branch_and_bound_rayon

[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 8, lights: [false, true, true, true, false, true, false, false], buttons: [[0, 2, 3, 4, 6, 7], [1, 2, 4, 5, 6], [1, 3, 4, 5, 7], [0, 2, 4], [4, 7], [0, 1, 4, 6], [1, 2, 3, 4, 5, 7], [2, 4, 7]], joltage: [29, 44, 42, 26, 66, 27, 30, 36] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 8, lights: [true, true, true, false, true, false, false, false], buttons: [[3, 4, 6], [1, 2, 3, 4, 5, 7], [0, 1, 2, 4], [0, 1, 3, 5, 7], [0, 1, 4, 5, 6, 7], [0, 2, 7], [4, 6], [7], [0, 6], [1, 4, 5, 6, 7]], joltage: [214, 221, 33, 36, 226, 204, 203, 217] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 8, lights: [true, true, false, true, false, true, true, true], buttons: [[0, 1, 7], [2, 3, 4, 5, 6, 7], [0, 3, 4, 5, 6, 7], [0, 1, 3, 5, 6, 7], [2, 7], [0, 1, 2, 3, 4, 6, 7], [0, 1, 3, 4, 6, 7]], joltage: [68, 52, 32, 65, 52, 36, 65, 88] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [false, true, false, true, false, false, false, true, false, false], buttons: [[0, 1, 4, 5, 9], [0, 2, 6, 7, 8, 9], [0, 5, 6, 9], [2, 5, 6], [1, 5, 9], [0, 1, 3, 4, 6, 7, 8, 9], [2], [0, 1, 2, 3, 4, 6, 8], [0, 7, 8, 9], [0, 1, 3, 5, 6, 7, 9], [3, 5, 9]], joltage: [68, 64, 220, 49, 46, 43, 59, 35, 36, 57] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [true, true, false, true, false, false, true], buttons: [[0, 2, 3, 4], [2, 3, 5], [0, 1, 3, 6], [0, 1, 3, 4, 5], [0, 1, 5, 6], [5]], joltage: [26, 16, 194, 197, 13, 205, 13] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [false, true, true, false, false, false, false, false, true, true], buttons: [[0, 1, 4, 7, 8, 9], [1, 3, 4, 5, 6, 9], [2, 4, 9], [3, 6, 8], [0, 2, 3, 4, 6, 7, 8], [0, 1, 2, 3, 4, 5, 6, 8], [1, 2, 3, 4, 6, 7, 8, 9], [2, 4, 6, 9], [0, 1, 5, 8, 9], [2, 7], [4, 6, 8, 9], [1, 3, 4, 5, 7, 8, 9], [1, 3, 4, 6, 7, 8, 9]], joltage: [12, 56, 55, 72, 88, 16, 88, 57, 85, 79] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [true, false, false, false, true], buttons: [[0, 2, 3, 4], [2, 3], [0, 1, 2, 3], [0, 1, 2]], joltage: [27, 21, 43, 41, 6] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [true, false, true, true, true], buttons: [[0, 1, 3], [1, 2, 3, 4], [1, 2, 4]], joltage: [4, 29, 25, 14, 25] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 43
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=3, misses=191
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 47.33µs
[2025-12-11T05:33:36Z INFO  day10] Completed 1/172 machines after 495.88µs
[2025-12-11T05:33:36Z INFO  day10] Found solution: 29
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=0, misses=55
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 46.96µs
[2025-12-11T05:33:36Z INFO  day10] Completed 2/172 machines after 511.38µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [false, false, true, false, true], buttons: [[0, 3], [1, 2, 4], [1, 2], [1, 2, 3, 4], [0, 2], [1, 4], [2, 3, 4]], joltage: [15, 32, 19, 17, 21] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 6, lights: [false, true, false, true, true, false], buttons: [[0, 2, 4], [1], [3, 4], [0, 1, 3, 4, 5], [0, 1, 2, 5], [1, 2]], joltage: [42, 46, 35, 25, 35, 32] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [true, true, false, false, true], buttons: [[0, 1, 2, 4], [1, 2, 3, 4], [0, 2, 3]], joltage: [141, 151, 155, 18, 151] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [false, false, true, true, false, false, false], buttons: [[0, 1, 2, 5, 6], [1, 2, 4, 6], [0, 1, 3, 5, 6], [0, 5], [1, 3, 5, 6], [0, 1, 2, 3, 4, 6], [5, 6], [4, 5]], joltage: [34, 37, 14, 35, 29, 64, 55] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 155
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=0, misses=311
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 112.33µs
[2025-12-11T05:33:36Z INFO  day10] Completed 3/172 machines after 770.63µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 6, lights: [true, false, true, false, true, true], buttons: [[0, 3], [5], [0, 1, 3], [0, 1, 2, 5], [0, 1, 2, 4, 5], [1, 3, 5], [0, 1, 2, 4], [1, 3, 4, 5]], joltage: [53, 66, 23, 56, 32, 52] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 205
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=958, misses=1626
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 480.58µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [true, false, false, false, false, true, true, false, true, false], buttons: [[5, 6, 8], [0, 2, 5, 6, 7, 9], [1, 3, 5, 6, 7, 9], [1, 2, 7, 9], [1, 2, 4, 5, 6, 7, 8, 9], [2, 8], [0, 2, 3, 5, 6, 7, 8, 9], [0, 4, 5, 9], [4, 5, 8], [4, 5], [0, 2, 3, 4, 5, 7, 8, 9], [0], [1, 2, 3, 4, 5, 6, 7, 8]], joltage: [49, 233, 86, 233, 57, 297, 253, 271, 72, 271] }
[2025-12-11T05:33:36Z INFO  day10] Completed 4/172 machines after 896.63µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 4, lights: [true, true, true, false], buttons: [[0, 2], [0, 2, 3], [2, 3], [0, 1], [3]], joltage: [40, 15, 38, 38] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 53
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=27, misses=181
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 26.54µs
[2025-12-11T05:33:36Z INFO  day10] Completed 5/172 machines after 937.71µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [false, true, false, false, true], buttons: [[0, 2, 3, 4], [0, 1, 3], [1, 4]], joltage: [30, 21, 12, 30, 15] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 33
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=0, misses=55
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 11.92µs
[2025-12-11T05:33:36Z INFO  day10] Completed 6/172 machines after 959.17µs
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [true, true, true, true, false], buttons: [[0, 1, 4], [1, 2, 3], [2, 3, 4], [1, 3], [0, 3]], joltage: [24, 12, 4, 30, 9] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 47
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=1238, misses=1681
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 400.25µs
[2025-12-11T05:33:36Z INFO  day10] Found solution: 30
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=107, misses=256
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 70.92µs
[2025-12-11T05:33:36Z INFO  day10] Completed 7/172 machines after 1.04ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [false, false, true, false, true, false, true], buttons: [[4, 6], [2, 5], [0, 2], [0, 1, 2, 3, 6], [1, 2, 4, 5, 6], [0, 2, 3, 4, 6], [0, 4]], joltage: [45, 16, 57, 23, 49, 23, 43] }
[2025-12-11T05:33:36Z INFO  day10] Completed 8/172 machines after 1.05ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 6, lights: [false, false, false, true, true, true], buttons: [[1, 2], [4, 5], [0, 3, 4], [0, 2, 3, 5], [0, 1, 2, 5]], joltage: [36, 11, 27, 29, 27, 37] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 46
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=758, misses=1763
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 731.42µs
[2025-12-11T05:33:36Z INFO  day10] Completed 9/172 machines after 1.43ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 6, lights: [false, false, true, true, false, true], buttons: [[0, 1, 3, 5], [0], [1, 2, 5], [3, 4], [0, 1, 3, 4], [1, 2, 3, 5], [3, 5], [0, 1, 5]], joltage: [67, 69, 19, 60, 37, 51] }
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [true, true, false, true, true, false, false, true, true, true], buttons: [[3, 5, 6, 7, 8, 9], [0, 1, 2, 3, 5, 7, 9], [0, 5, 8], [2, 4, 5, 8], [2, 3, 6, 7], [0, 1, 2, 3, 6, 7, 8], [0, 1, 2, 4, 5, 6, 8], [5, 6, 7]], joltage: [55, 54, 73, 53, 39, 97, 75, 73, 75, 37] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 37
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=2636, misses=3538
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 2.72ms
[2025-12-11T05:33:36Z INFO  day10] Completed 10/172 machines after 3.91ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [false, true, false, false, false, true, true, false, true, true], buttons: [[0, 1, 2, 5, 7, 8], [1, 5, 6, 8, 9], [0, 1, 2, 6, 8], [0, 8, 9], [0, 7], [1, 9], [1, 3, 8], [1, 5, 7], [0, 1, 2, 3, 4, 7, 8]], joltage: [39, 69, 24, 40, 20, 11, 6, 28, 62, 36] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 76
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=75, misses=402
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 104.88µs
[2025-12-11T05:33:36Z INFO  day10] Completed 11/172 machines after 4.04ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 8, lights: [false, false, false, true, true, true, false, true], buttons: [[0, 2, 3, 6], [0, 1, 3, 4, 5, 6, 7], [0, 2, 4, 6], [0, 1, 2, 3, 6], [3, 4, 5, 7], [1, 3, 4, 6, 7]], joltage: [56, 33, 48, 55, 29, 11, 63, 18] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 66
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=5808, misses=7417
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 4.41ms
[2025-12-11T05:33:36Z INFO  day10] Completed 12/172 machines after 5.64ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [false, true, false, false, true], buttons: [[1, 2, 4], [2, 3], [0], [1, 4], [3], [3, 4], [0, 1, 2]], joltage: [23, 28, 26, 33, 26] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 60
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=7146, misses=19282
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 6.77ms
[2025-12-11T05:33:36Z INFO  day10] Found solution: 37
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=9575, misses=10767
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 3.53ms
[2025-12-11T05:33:36Z INFO  day10] Completed 13/172 machines after 9.85ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [true, true, true, false, true, false, true], buttons: [[0, 2, 3, 4, 6], [0, 4, 5, 6], [3, 4, 5, 6], [0, 2], [1, 4, 5, 6]], joltage: [39, 14, 23, 178, 208, 197, 208] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 97
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=7795, misses=21797
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 6.92ms
[2025-12-11T05:33:36Z INFO  day10] Completed 14/172 machines after 10.83ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [true, false, true, true, true, false, true], buttons: [[1, 2, 4, 5], [0, 2, 3, 4], [1, 2, 3, 5, 6], [0, 2], [0, 1, 3, 6], [0, 1, 2, 6]], joltage: [151, 134, 151, 33, 11, 11, 134] }
[2025-12-11T05:33:36Z INFO  day10] Completed 15/172 machines after 11.53ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 8, lights: [false, false, false, false, false, false, true, true], buttons: [[0, 1, 2, 4, 6, 7], [0, 1, 2, 4, 5], [0, 2, 3, 4, 5, 7], [0, 1, 4, 5, 7], [0, 1, 2, 3, 6, 7], [0, 1, 2], [6, 7], [0, 1, 3, 6]], joltage: [91, 80, 63, 32, 60, 42, 50, 65] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 209
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=3807, misses=4862
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 8.39ms
[2025-12-11T05:33:36Z INFO  day10] Found solution: 64
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=47887, misses=33096
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 17.85ms
[2025-12-11T05:33:36Z INFO  day10] Completed 16/172 machines after 18.99ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 9, lights: [false, false, true, true, false, true, false, true, true], buttons: [[0, 2, 5, 7], [1, 2, 3, 6, 8], [0, 1, 4, 6, 7], [5, 7, 8], [0, 1, 3, 4, 6, 7, 8], [0, 5], [3, 5, 7], [1, 3, 4, 5, 6], [2, 3, 4, 8], [0, 1, 4, 5, 7], [0, 1, 3, 5, 6, 8]], joltage: [67, 79, 51, 89, 68, 93, 75, 87, 72] }
[2025-12-11T05:33:36Z INFO  day10] Completed 17/172 machines after 21.90ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 4, lights: [true, true, false, false], buttons: [[2], [0, 3], [0, 1, 3], [0, 1]], joltage: [19, 7, 12, 12] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 31
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=49, misses=107
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 21.33µs
[2025-12-11T05:33:36Z INFO  day10] Completed 18/172 machines after 21.94ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 5, lights: [false, true, false, true, false], buttons: [[0, 1, 4], [1, 3], [0, 2, 3], [2, 3, 4]], joltage: [29, 25, 205, 214, 208] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 229
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=5369, misses=6296
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 1.33ms
[2025-12-11T05:33:36Z INFO  day10] Completed 19/172 machines after 23.37ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 9, lights: [true, true, true, false, true, false, true, true, false], buttons: [[0, 1, 2, 5, 6, 7, 8], [2, 4, 5, 6], [1, 3, 4, 5, 6], [1, 4, 5, 7, 8], [0, 2, 3, 5, 6, 7, 8], [0, 2, 3, 4, 6], [0, 3, 4, 8], [7], [0, 2, 5]], joltage: [71, 35, 55, 65, 65, 78, 52, 52, 57] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 64
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=59116, misses=47414
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 20.99ms
[2025-12-11T05:33:36Z INFO  day10] Completed 20/172 machines after 28.07ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [false, false, false, false, false, true, true, false, false, false], buttons: [[0, 1, 2, 3, 4, 5, 6, 7], [9], [1, 4, 5, 6, 7, 8, 9], [0, 1, 3, 4, 8, 9], [0, 2, 3, 6, 8], [0, 2], [5, 6, 9], [1, 3, 4, 6, 8, 9], [1, 3, 4, 5, 6, 8, 9], [0, 1, 2, 3, 5, 6, 8, 9], [1, 2, 4, 5, 6, 7, 8, 9], [0, 5, 8], [3, 5, 6, 8]], joltage: [48, 77, 30, 85, 62, 82, 99, 11, 99, 107] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 162
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=26488, misses=57440
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 21.73ms
[2025-12-11T05:33:36Z INFO  day10] Completed 21/172 machines after 34.41ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 10, lights: [false, true, true, true, false, false, true, true, false, true], buttons: [[1, 2, 3, 4, 5, 6, 8, 9], [8, 9], [0, 1, 2, 3, 5, 8, 9], [1, 2, 3, 4, 9], [0, 1, 3, 4, 5, 7, 8, 9], [3, 5, 6, 9], [1, 2, 3, 5, 6, 7, 9], [0, 2, 3, 4, 6, 7, 8, 9], [0, 2, 3, 6], [0, 1, 2, 5, 6], [1, 3, 4, 5, 7, 8], [0, 1, 3, 6, 8, 9]], joltage: [46, 82, 72, 101, 68, 70, 60, 45, 62, 95] }
[2025-12-11T05:33:36Z INFO  day10] Found solution: 66
[2025-12-11T05:33:36Z INFO  day10] Memo stats: hits=237547, misses=155579
[2025-12-11T05:33:36Z INFO  day10] Elapsed time: 117.22ms
[2025-12-11T05:33:36Z INFO  day10] Completed 22/172 machines after 124.06ms
[2025-12-11T05:33:36Z INFO  day10] Working on Machine { size: 7, lights: [true, true, false, true, false, false, false], buttons: [[3, 4, 5], [0, 3, 4, 5], [0, 1, 2, 5, 6], [0, 2], [2, 3, 4, 6], [0, 1, 4, 5], [1, 2, 5, 6], [0, 1, 3], [0, 3, 4, 5, 6]], joltage: [74, 33, 19, 53, 45, 43, 16] }
[2025-12-11T05:33:37Z INFO  day10] Found solution: 86
[2025-12-11T05:33:37Z INFO  day10] Memo stats: hits=1162560, misses=1268171
[2025-12-11T05:33:37Z INFO  day10] Elapsed time: 717.54ms
[2025-12-11T05:33:37Z INFO  day10] Completed 23/172 machines after 813.30ms
[2025-12-11T05:33:37Z INFO  day10] Working on Machine { size: 10, lights: [false, false, false, false, false, true, true, false, true, true], buttons: [[7, 9], [0, 2, 3, 4, 5, 6, 7, 8], [1, 3, 4, 5, 6, 7, 8, 9], [0, 1, 4, 8], [2, 6], [0, 3, 4, 5, 8], [3, 4, 5, 7, 8], [1, 2, 3, 5, 6, 7, 8], [0, 3, 4, 6, 7, 8], [0, 8], [1, 2, 3, 4, 6]], joltage: [31, 52, 39, 48, 64, 34, 53, 33, 55, 15] }
[2025-12-11T05:33:38Z INFO  day10] Found solution: 91
[2025-12-11T05:33:38Z INFO  day10] Memo stats: hits=1920758, misses=2301548
[2025-12-11T05:33:38Z INFO  day10] Elapsed time: 1.73s
[2025-12-11T05:33:38Z INFO  day10] Found solution: 74
[2025-12-11T05:33:38Z INFO  day10] Memo stats: hits=1558944, misses=2743455
[2025-12-11T05:33:38Z INFO  day10] Elapsed time: 1.75s
[2025-12-11T05:33:38Z INFO  day10] Completed 24/172 machines after 1.92s
[2025-12-11T05:33:38Z INFO  day10] Working on Machine { size: 10, lights: [false, true, true, false, false, true, true, true, true, false], buttons: [[0, 3, 4, 6, 9], [0, 1, 2, 3, 5, 6, 7, 8, 9], [3, 4], [0, 3, 7, 8, 9], [0, 1, 2, 5, 6, 7, 9], [1, 3, 4, 5, 6, 8, 9], [4, 7], [1, 3, 6, 8, 9], [0, 1, 2, 3, 4, 5, 8], [6, 7]], joltage: [61, 32, 27, 62, 56, 32, 35, 41, 36, 52] }
[2025-12-11T05:33:38Z INFO  day10] Completed 25/172 machines after 2.15s
[2025-12-11T05:33:38Z INFO  day10] Working on Machine { size: 10, lights: [true, false, false, false, false, false, false, false, false, false], buttons: [[1, 3, 4, 7], [1, 4, 5, 7, 8], [0, 1, 2, 3, 5, 7, 9], [4, 5], [2, 3, 9], [0, 1, 2, 3, 6, 7, 8, 9], [3, 6, 9], [0, 1, 4, 6, 7, 8], [0, 4, 9], [1, 2, 3, 6], [5, 7, 8, 9], [6]], joltage: [36, 70, 32, 60, 49, 33, 64, 58, 35, 45] }
[2025-12-11T05:33:40Z INFO  day10] Found solution: 88
[2025-12-11T05:33:40Z INFO  day10] Memo stats: hits=1715277, misses=5244782
[2025-12-11T05:33:40Z INFO  day10] Elapsed time: 3.48s
[2025-12-11T05:33:40Z INFO  day10] Completed 26/172 machines after 3.91s
[2025-12-11T05:33:40Z INFO  day10] Working on Machine { size: 6, lights: [true, false, false, true, true, false], buttons: [[0, 1, 4], [1, 2, 4], [0, 1, 2, 3], [1, 5]], joltage: [13, 42, 20, 0, 33, 9] }
[2025-12-11T05:33:40Z INFO  day10] Found solution: 42
[2025-12-11T05:33:40Z INFO  day10] Memo stats: hits=0, misses=76
[2025-12-11T05:33:40Z INFO  day10] Elapsed time: 17.13µs
[2025-12-11T05:33:40Z INFO  day10] Completed 27/172 machines after 3.91s
[2025-12-11T05:33:40Z INFO  day10] Working on Machine { size: 6, lights: [true, true, true, false, false, false], buttons: [[0, 1, 2], [1, 2, 4, 5], [2, 3, 5], [1, 3, 5], [1], [1, 2, 3]], joltage: [199, 238, 232, 27, 12, 38] }
[2025-12-11T05:33:40Z INFO  day10] Found solution: 238
[2025-12-11T05:33:40Z INFO  day10] Memo stats: hits=26, misses=445
[2025-12-11T05:33:40Z INFO  day10] Elapsed time: 74.29µs
[2025-12-11T05:33:40Z INFO  day10] Completed 28/172 machines after 3.91s
[2025-12-11T05:33:40Z INFO  day10] Working on Machine { size: 10, lights: [false, true, false, false, true, false, false, false, true, false], buttons: [[1, 8, 9], [2, 3], [1, 2, 4, 6, 7], [0, 1, 2, 3, 4, 7, 8], [1, 2, 3, 5, 6, 7, 8, 9], [1, 2, 7], [1, 2, 7, 9], [2, 3, 4, 5, 7, 8, 9], [1, 3, 5, 6, 7, 9], [0, 2, 3, 5, 7, 8, 9], [0, 2, 3, 4, 6, 8]], joltage: [24, 64, 85, 71, 35, 52, 39, 83, 58, 76] }
...
```

Letting that run for more than an hour, it managed to get through some 120 of them. There are still ones that even this isn't managing to solve. And, given that I *know* how to solve this one quickly if I just give up and use an external program...

## Part 2 - Just use z3

Okay. Let's just give up and use [z3](https://github.com/Z3Prover/z3).

```rust
impl Machine {
    fn solve_joltage_z3(&self) -> usize {
        log::info!("Working on {self:?}");

        let mut buffer = String::new();

        buffer.push_str("(set-option :produce-models true)\n");
        buffer.push_str("(set-logic QF_LIA)\n");

        // Our variables are how many times each button is pressed
        for i in 0..self.buttons.len() {
            buffer.push_str(&format!("(declare-const p{i} Int)\n"));
            buffer.push_str(&format!("(assert (>= p{i} 0))\n"));
        }

        // Each joltage has to end up exactly matching pi * if button[i] contains it
        for idx in 0..self.size {
            let mut terms: Vec<String> = vec![];
            for (bi, button) in self.buttons.iter().enumerate() {
                if button.contains(&idx) {
                    terms.push(format!("p{bi}"));
                }
            }
            let sum = if terms.is_empty() {
                "0".to_string()
            } else {
                format!("(+ {})", terms.join(" "))
            };
            buffer.push_str(&format!("(assert (= {} {}))\n", sum, self.joltage[idx]));
        }

        // Our objective is to minimize the total presses
        let total = (0..self.buttons.len())
            .map(|i| format!("p{i}"))
            .collect::<Vec<_>>()
            .join(" ");

        buffer.push_str(&format!("(minimize (+ {total}))\n"));

        buffer.push_str("(check-sat)\n");
        buffer.push_str("(get-model)\n");

        log::debug!("Z3 input:\n{buffer}");

        let f = {
            let mut f = NamedTempFile::new().expect("failed to create temp file for z3");
            f.write_all(buffer.as_bytes())
                .expect("failed to write z3 input to temp file");
            f
        };

        // Now call Z3 on it
        let output = std::process::Command::new("z3")
            .arg(f.path().to_str().unwrap())
            .output()
            .expect("failed to execute z3");

        // Parse output
        // sat
        // (
        //   (define-fun p5 () Int
        //     0)
        // ...
        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut total_presses = 0;

        log::debug!("Z3 output:\n{stdout}");

        let mut lines = stdout.lines();
        while let Some(line) = lines.next() {
            if line.contains("(define-fun") {
                let next_line = lines.next().unwrap();
                let presses: usize = next_line
                    .trim()
                    .trim_end_matches(')')
                    .parse()
                    .expect("failed to parse presses");

                total_presses += presses;
            }
        }
        log::info!("Found solution: {total_presses}");

        total_presses
    }
}

#[aoc::register]
fn part2_z3(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .map(|m| m.solve_joltage_z3())
        .sum::<usize>()
        .to_string()
}

#[aoc::register]
fn part2_z3_rayon(input: &str) -> impl Into<String> {
    input
        .lines()
        .map(Machine::from)
        .par_bridge()
        .map(|m| m.solve_joltage_z3())
        .sum::<usize>()
        .to_string()
}
```

So basically this is just formulating this as a series of constraints, like this:

```bash
$ head -n 1 input/2025/day10.txt | RUST_LOG=debug cargo run --release --bin day10 run part2_z3 -

    Finished `release` profile [optimized] target(s) in 0.04s
     Running `target/release/day10 run part2_z3 -`
[2025-12-11T05:11:48Z INFO  day10] Working on Machine { size: 8, lights: [false, true, true, true, false, true, false, false], buttons: [[0, 2, 3, 4, 6, 7], [1, 2, 4, 5, 6], [1, 3, 4, 5, 7], [0, 2, 4], [4, 7], [0, 1, 4, 6], [1, 2, 3, 4, 5, 7], [2, 4, 7]], joltage: [29, 44, 42, 26, 66, 27, 30, 36] }
[2025-12-11T05:11:48Z DEBUG day10] Z3 input:
    (set-option :produce-models true)
    (set-logic QF_LIA)
    (declare-const p0 Int)
    (assert (>= p0 0))
    (declare-const p1 Int)
    (assert (>= p1 0))
    (declare-const p2 Int)
    (assert (>= p2 0))
    (declare-const p3 Int)
    (assert (>= p3 0))
    (declare-const p4 Int)
    (assert (>= p4 0))
    (declare-const p5 Int)
    (assert (>= p5 0))
    (declare-const p6 Int)
    (assert (>= p6 0))
    (declare-const p7 Int)
    (assert (>= p7 0))
    (assert (= (+ p0 p3 p5) 29))
    (assert (= (+ p1 p2 p5 p6) 44))
    (assert (= (+ p0 p1 p3 p6 p7) 42))
    (assert (= (+ p0 p2 p6) 26))
    (assert (= (+ p0 p1 p2 p3 p4 p5 p6 p7) 66))
    (assert (= (+ p1 p2 p6) 27))
    (assert (= (+ p0 p1 p5) 30))
    (assert (= (+ p0 p2 p4 p6 p7) 36))
    (minimize (+ p0 p1 p2 p3 p4 p5 p6 p7))
    (check-sat)
    (get-model)

[2025-12-11T05:11:48Z DEBUG day10] Z3 output:
    sat
    (
      (define-fun p2 () Int
        0)
      (define-fun p6 () Int
        20)
      (define-fun p3 () Int
        6)
      (define-fun p7 () Int
        3)
      (define-fun p4 () Int
        7)
      (define-fun p0 () Int
        6)
      (define-fun p1 () Int
        7)
      (define-fun p5 () Int
        17)
    )

[2025-12-11T05:11:48Z INFO  day10] Found solution: 66
66
```

Each `p0`, `p1`, ... is how many 'presses' we are making, so they're each `>= 0`. Then for each target joltage, we sum the presses that contribute towards that value. THen finally, minimize the sum. 

That's... it? 

And it's even faster than part 1:

```bash
$ just run-and-bench 10 part2_z3_rayon 10

17424

part2_z3_rayon: 129.899304ms ± 2.541906ms [min: 125.474959ms, max: 133.146667ms, median: 131.154084ms]
```

That is just not that satisfying. 

## [12/11] Part 2 - Equations continued

And so we go down the rabbit hole. 

So this is basically the continuation of yesterdays work with [equations](#edit-part-2---equations-continued). Basically:

1. For each machine, generate a set of equations of the form 

    $$c_1 p_1 + c_2 p_2 + ... = C$$

2. Several time, expand those equations by adding each set of equations pairwise
3. Any time we end up with an expression exactly like

 $$c_1 p_1 = C$$

 We know that $$p_1 = \frac{C}{c_1}$$. 

4. Any time we have all positive or negative values on an equation, it gives an upper bound 

    So for the above equation (if all coefficients are positive), we know that 

    $$p_1 \le \frac{C}{c_1}$$

5. Start the solver as we did before, except:
6. Any time we have a known value (from step 3), immediately assign that value
7. Any time we have *any* equation where all but one `c_n` is known, assign that last value
8. Iterate each remaining value recursively starting with the lowest bounds

So in parts, first we create the equations:

```rust
let mut equations: HashSet<Equation> = HashSet::new();
for idx in 0..self.size {
    let mut coefficients = vec![0; self.buttons.len()];
    for (bi, button) in self.buttons.iter().enumerate() {
        if button.contains(&idx) {
            coefficients[bi] = 1;
        }
    }
    equations.insert(Equation {
        constant: self.joltage[idx] as isize,
        coefficients,
    });
}
```

Then we expand that list, setting bounds:

```rust
for _i in 0..3 {
    tracing::info!(
        "[{machine_id}] Expanding equations, iter={_i}, count={}",
        equations.len()
    );

    let initial_equations = equations.clone();
    let initial_size = equations.len();

    for eq1 in initial_equations.iter() {
        for eq2 in initial_equations.iter() {
            if eq1 != eq2 {
                equations.insert(eq1.clone() + eq2.clone());
                equations.insert(eq1.clone().negated() + eq2.clone());
                equations.insert(eq2.clone().negated() + eq1.clone());
            }
        }
    }
    if equations.len() == initial_size {
        break;
    }

    // Look for any single-variable equations
    let single_var_eqs: Vec<Equation> = equations
        .iter()
        .filter(|eq| eq.coefficients.iter().filter(|&&c| c != 0).count() == 1)
        .cloned()
        .collect();

    tracing::info!(
        "[{machine_id}] Found {} single-variable equations",
        single_var_eqs.len()
    );
    for eq in single_var_eqs.iter() {
        tracing::info!("  {eq}");
    }

    // Record known values
    for eq in single_var_eqs.iter() {
        let xi = eq.coefficients.iter().position(|&c| c != 0).unwrap();

        assert!(eq.constant % eq.coefficients[xi] == 0);
        bounds[xi] = Bound::Known(eq.constant / eq.coefficients[xi]);
    }
    tracing::info!("[{machine_id}] Known values so far: {bounds:?}");

    // Apply known values to all equations
    let known_values = bounds
        .iter()
        .map(|b| match b {
            Bound::Known(v) => Some(*v as usize),
            _ => None,
        })
        .collect::<Vec<_>>();
    let updated_equations: HashSet<Equation> =
        equations.iter().map(|eq| eq.apply(&known_values)).collect();
    equations = updated_equations;

    // For any equation with only positive co-efficients, we can set bounds
    // Assume that we put as much as possible into each variable for bound
    for eq in equations.iter() {
        // All negative is all positive, just... opposite!
        let eq = if eq.coefficients.iter().all(|&c| c <= 0) {
            eq.negated()
        } else {
            eq.clone()
        };

        if !eq.coefficients.iter().all(|&c| c >= 0) {
            continue;
        }

        if eq.constant <= 0 {
            continue;
        }

        for (i, coef) in eq.coefficients.iter().enumerate() {
            if *coef == 0 {
                continue;
            }

            let max_times = eq.constant / *coef;
            match &bounds[i] {
                // Previously unknown bounds now have a maximum value
                Bound::Unknown => {
                    bounds[i] = Bound::Bounded(0, max_times);
                }
                // If this sets a better upper bound, yay?
                Bound::Bounded(l, u) => {
                    if *u > max_times {
                        bounds[i] = Bound::Bounded(*l, max_times);
                    }
                }
                // Known bounds don't need to change
                // Hopefully this doesn't prove our bounds are wrong :smile:
                Bound::Known(_) => {}
            };
        }
    }

    // Remove all equations that still depend on known variables
    // Because of the apply step above, these should be zeroed out
    let filtered_equations: HashSet<Equation> = equations
        .iter()
        .filter(|eq| {
            eq.coefficients
                .iter()
                .enumerate()
                .all(|(i, &c)| !(c != 0 && matches!(bounds[i], Bound::Known(_))))
        })
        .cloned()
        .collect();
    equations = filtered_equations;
}
```

Then we have our recursive solver:

```rust
#[tracing::instrument(skip(machine, bounds, equations))]
fn helper(
    machine: &Machine,
    presses: &Vec<Option<usize>>,
    bounds: &Vec<Bound>,
    equations: &HashSet<Equation>,
) -> Option<usize> {
    let machine_id = machine.id;

    // If the currently known presses make for an impossible voltage, fail
    // If we went beyond the bounds without finding an answer, fail
    let mut current = vec![0; machine.size];
    for (press, button) in presses.iter().zip(machine.buttons.iter()) {
        if let Some(p) = press {
            for b in button {
                current[*b] += p;
            }
        }
    }

    log::debug!(
        "[{machine_id}] helper({presses:?}) => {current:?} vs {:?}",
        machine.joltage
    );

    // If we have exactly the right current, this is the correct solution
    if current == machine.joltage {
        log::debug!("[{machine_id}] Found an answer!: {presses:?}");
        let press_total = presses.iter().map(|v| v.unwrap_or(0)).sum::<usize>();
        return Some(press_total);
    }

    if current
        .iter()
        .zip(machine.joltage.iter())
        .any(|(c, j)| c > j)
    {
        log::debug!("[{machine_id}] OVER JOLTAGE");
        return None;
    }

    // If we made it this far and all presses are set, this solution is under joltage
    if presses.iter().all(|f| f.is_some()) {
        log::debug!("[{machine_id}] under joltage :(");
        return None;
    }

    // If we have any equation where all but 1 variable is known, we can set the last one
    for eq in equations.iter() {
        let unknown_vars: Vec<usize> = eq
            .coefficients
            .iter()
            .enumerate()
            .filter(|(i, _)| presses[*i].is_none() && eq.coefficients[*i] != 0)
            .map(|(i, _)| i)
            .collect();

        if unknown_vars.len() == 1 {
            let xi = unknown_vars[0];
            let mut sum_known = 0isize;
            for (i, &coef) in eq.coefficients.iter().enumerate() {
                if i != xi
                    && let Some(p) = presses[i] {
                        sum_known += coef * (p as isize);
                    }
            }

            let required_xi = (eq.constant - sum_known) / eq.coefficients[xi];
            if required_xi < 0 {
                log::debug!(
                    "[{machine_id}] Negative press violation on equation {eq} with {presses:?}"
                );
                return None;
            }

            let mut new_presses = presses.clone();
            new_presses[xi] = Some(required_xi as usize);
            log::debug!(
                "[{machine_id}] Applying equation {eq}, {presses:?} => {new_presses:?}"
            );
            return helper(
                machine,
                &new_presses,
                bounds,
                equations,
            );
        }
    }

    // The current index is the unset press with the lowest range
    let mut current_idx = 0;
    let mut best_size = isize::MAX;
    for (i, p) in presses.iter().enumerate() {
        if p.is_some() {
            continue;
        }

        let range_size = match bounds[i] {
            Bound::Unknown => isize::MAX,
            Bound::Bounded(lo, hi) => hi - lo + 1,
            Bound::Known(_) => 1,
        };

        if range_size < best_size {
            current_idx = i;
            best_size = range_size;
        }
    }
    tracing::debug!("[{machine_id}] Selected {current_idx} as the next index");

    // Test each value at the current idx, finding the best recursive answer
    let mut best = None;

    match bounds[current_idx] {
        Bound::Unknown => {
            // Not sure how I can end up here, but it's possible?
            // Hopefully we'll eventually find an answer
            for value in 0.. {
                let mut next_presses = presses.clone();
                next_presses[current_idx] = Some(value as usize);
                let result = helper(
                    machine,
                    &next_presses,
                    bounds,
                    equations,
                );

                if best.is_none() {
                    best = result;
                } else if result.is_some() {
                    best = Some(best.unwrap().min(result.unwrap()));
                }
            }
        }
        Bound::Bounded(lo, hi) => {
            for value in lo..=hi {
                let mut next_presses = presses.clone();
                next_presses[current_idx] = Some(value as usize);
                let result = helper(
                    machine,
                    &next_presses,
                    bounds,
                    equations,
                );

                if best.is_none() {
                    best = result;
                } else if result.is_some() {
                    best = Some(best.unwrap().min(result.unwrap()));
                }
            }
        }
        Bound::Known(v) => {
            let mut next_presses = presses.clone();
            next_presses[current_idx] = Some(v as usize);
            best = helper(
                machine,
                &next_presses,
                bounds,
                equations,
            );
        }
    }

    best
}
```

which we can kick off easy enough:

```rust
tracing::info!("[{machine_id}] Starting recursive search");
let result = helper(
    self,
    &vec![None; self.buttons.len()],
    &bounds,
    &equations,
);
```

And... it works!

```text
$ cargo run --release --bin day10 -- run part2_eqn_rayon input/2025/day10.txt

17424

$ cargo run --release --bin day10 -- bench part2_eqn_rayon --warmup 0 --iters 1 input/2025/day10.txt

part2_eqn_rayon: 79.115645459s ± 0ns [min: 79.115645459s, max: 79.115645459s, median: 79.115645459s]
```

Digging into the debugging a bit more (it's fun to watch), the longest machine in my input was line 97 (zero based) taking 65.22s. There were fewer than the number of cores I had machines that took more than a minute, so the parallelization really worked out. 

That's still more than a minute, but given that the time was basically ∞ before... that's not actually that bad. I expect I'm still doing a *ton* of allocations and work I probably don't have to. So I could really tune this down more. But at this point, I solved it fast (z3) and without libraries (other than rayon for free parallelization). Pretty good to me!

## Benchmarks

This one is a mess.

```bash
$ just run-and-bench 10 part1 10

452

part1: 1.212226433s ± 13.832532ms [min: 1.199442042s, max: 1.247776833s, median: 1.208264834s]

$ just run-and-bench 10 part1_rayon 10

452

part1_rayon: 331.882295ms ± 5.14392ms [min: 324.905666ms, max: 342.0265ms, median: 331.103208ms]

$ just run-and-bench 10 part2_z3_rayon 10

17424

part2_z3_rayon: 129.899304ms ± 2.541906ms [min: 125.474959ms, max: 133.146667ms, median: 131.154084ms]

$ cargo run --release --bin day10 -- bench part2_eqn_rayon --warmup 0 --iters 1 input/2025/day10.txt

part2_eqn_rayon: 79.115645459s ± 0ns [min: 79.115645459s, max: 79.115645459s, median: 79.115645459s]
```

| Day | Part | Solution          | Benchmark                  |
| --- | ---- | ----------------- | -------------------------- |
| 10  | 1    | `part1`           | 1.212226433s ± 13.832532ms |
| 10  | 1    | `part1_rayon`     | 331.882295ms ± 5.14392ms   |
| 10  | 2    | `part2_z3_rayon`  | 129.899304ms ± 2.541906ms  |
| 10  | 2    | `part2_eqn_rayon` | 79.115645459s ± 0ns        |

I ... can do better. We'll see if/when I come back to this one. 