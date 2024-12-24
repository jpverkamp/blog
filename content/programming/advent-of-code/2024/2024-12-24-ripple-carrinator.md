---
title: "AoC 2024 Day 24: Ripple Carrinator"
date: 2024-12-24 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics: 
- Circuit design
- Graph theory
---
## Source: [Day 24: Crossed Wires](https://adventofcode.com/2024/day/24)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day24.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a collection of gates of the form `arg0 (AND|OR|XOR) arg2 -> out` and input values of form `x**` and `y**`, what is the value of `z**` interpreted as a binary number?

<!--more-->

Okay, first we're going to represent `Operators` and `Wires`:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Operator {
    And,
    Or,
    Xor,
}

impl From<&str> for Operator {
    fn from(value: &str) -> Self {
        match value.to_ascii_uppercase().as_str() {
            "AND" => Self::And,
            "OR" => Self::Or,
            "XOR" => Self::Xor,
            _ => panic!("Invalid operator: {}", value),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Wire<'input> {
    Input(bool),
    Function(Operator, &'input str, &'input str),
}
```

Then store these in a `Machine` with parsing:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Machine<'input> {
    wires: HashMap<&'input str, Wire<'input>>,
}

impl<'input> From<&'input str> for Machine<'input> {
    fn from(input: &'input str) -> Self {
        let mut wires = HashMap::new();

        for line in input.lines() {
            if line.contains(':') {
                let (key, value) = line.split_once(": ").unwrap();
                let value = value == "1";

                wires.insert(key, Wire::Input(value));
            }

            if line.contains("->") {
                let mut parts = line.split_ascii_whitespace();
                let arg0 = parts.next().unwrap();
                let op = parts.next().unwrap().into();
                let arg1 = parts.next().unwrap();
                parts.next(); // Skip the ->
                let result = parts.next().unwrap();

                wires.insert(result, Wire::Function(op, arg0, arg1));
            }
        }

        Self { wires }
    }
}
```

Now, we have a pair of functions. One will recursively determine the value of a single output wire:

```rust
impl<'input> Machine<'input> {
    pub fn value_of(&self, wire: &'input str) -> bool {
        match self.wires.get(wire).unwrap() {
            Wire::Input(value) => *value,
            Wire::Function(op, arg0, arg1) => {
                let arg0 = self.value_of(arg0);
                let arg1 = self.value_of(arg1);

                match op {
                    Operator::And => arg0 & arg1,
                    Operator::Or => arg0 | arg1,
                    Operator::Xor => arg0 ^ arg1,
                }
            }
        }
    }
}
```

And the other will take all wires with a specific prefix, sort them, and combine that into a binary number:

```rust
impl<'input> Machine<'input> {
    pub fn value_of_prefixed(&'input self, prefix: char) -> usize {
        let mut binary = String::new();

        for wire in self.wires().sorted().rev() {
            if wire.starts_with(prefix) {
                binary.push(if self.value_of(wire) { '1' } else { '0' });
            }
        }

        usize::from_str_radix(&binary, 2).unwrap()
    }
}
```

That's a long way of saying the problem is...

```rust
#[aoc(day24, part1, v1)]
fn part1_v1(input: &str) -> u128 {
    let machine = Machine::from(input);
    machine.value_of_prefixed('z') as u128
}
```

Originally, I had a `value_of` function that took `&mut self` and would cache the values of each wire as we calculated it, so we don't have to recursively calculate values more than once, but it turns out...

```bash
$ cargo aoc --day 24 --part 1

AOC 2024
Day 24 - Part 1 - v1 : 60714423975686
	generator: 416ns,
	runner: 338.709µs
```

It's already sub-millisecond. It's not really necessary. 

## Part 2

> Your circuit is supposed to implement a [[wiki:ripple carry adder]](), but 4 pairs of wires have been swapped. Find those four pairs; output them sorted and comma delimited. 

### Brute force

All right. I know it's not going to work, but let's implement it anyways!

First, the ability to swap two wires:

```rust
impl<'input> Machine<'input> {
    pub fn swap(&mut self, a: &'input str, b: &'input str) {
        let old_b = self.wires[b];
        let old_a = self.wires[a];

        self.wires.insert(a, old_b);
        self.wires.insert(b, old_a);
    }
}
```

And then try it:

```rust
#[aoc(day24, part2, bruteforce)]
fn part2_bruteforce(input: &str) -> String {
    let machine = Machine::from(input);

    let x = machine.value_of_prefixed('y');
    let y = machine.value_of_prefixed('x');
    let target_z = x + y;

    let mut dependency_cache = HashMap::new();
    for wire in machine.wires() {
        dependency_cache.insert(
            wire,
            machine
                .depends_on(wire)
                .iter()
                .copied()
                .collect::<HashSet<_>>(),
        );
    }

    let result = machine
        .wires
        .keys()
        .filter(|w| !w.starts_with('x') && !w.starts_with('y'))
        .permutations(8)
        .map(|wires| {
            let mut machine = machine.clone();
            machine.swap(wires[0], wires[1]);
            machine.swap(wires[2], wires[3]);
            machine.swap(wires[4], wires[5]);
            machine.swap(wires[6], wires[7]);

            if machine.value_of_prefixed_loopcheck('z')? == target_z {
                Ok(wires.iter().sorted().join(","))
            } else {
                Err(())
            }
        })
        .find(|result| result.is_ok())
        .unwrap()
        .unwrap();

    result
}
```

Keen eyed observers will notice that there's a slight difference: `value_of_prefixed_loopcheck`. That's because it's possible (likely even) for swapping any two wires to lead to a situation where you have loops in the wiring. 

```rust
impl<'input> Machine<'input> {
    pub fn value_of_prefixed_loopcheck(&'input self, prefix: char) -> Result<usize, ()> {
        let mut binary = String::new();

        for wire in self.wires().sorted().rev() {
            if wire.starts_with(prefix) {
                binary.push(if self.value_of_loopcheck(wire)? { '1' } else { '0' });
            }
        }

        usize::from_str_radix(&binary, 2).map_err(|e| ())
    }

    pub fn value_of_loopcheck(&self, wire: &'input str) -> Result<bool, ()> {
        fn recur<'input>(me: &Machine, wire: &'input str, checked: Vec<&str>) -> Result<bool, ()> {
            if checked.contains(&wire) {
                return Err(())
            }
            let mut next_checked = checked.clone();
            next_checked.push(wire);

            match me.wires.get(wire).unwrap() {
                Wire::Input(value) => Ok(*value),
                Wire::Function(op, arg0, arg1) => {
                    let arg0 = recur(me, arg0, next_checked.clone())?;
                    let arg1 = recur(me, arg1, next_checked.clone())?;

                    Ok(match op {
                        Operator::And => arg0 & arg1,
                        Operator::Or => arg0 | arg1,
                        Operator::Xor => arg0 ^ arg1,
                    })
                }
            }
        }

        recur(self, wire, vec![])
    }
}
```

In both cases, we spend the extra effort to check if we every visit the same wire more than once, returning an `Err` if we do. 

Unfortunately, there are a *ton* of combinations to check if we're going to check them all...

```bash
$ cat input/2024/day24.txt \
    | egrep -o '\w{3}' \
    | egrep -v '^x|^y|AND|OR|XOR' \
    | sort | uniq | wc -l

222
```

$$P(222, 8) = \frac{222!}{(222-8)!} \approx 5.2 x 10^18$$ 

That's 5 quintillion. If you could evaluate a case every nanosecond (which is at least an order of magnitude too fast), it would take 60,000 days to check all of those. That's 164 years.

Yeah, I'm not just going to let that one run. 

### Visualizing the problem

Okay. Let's actually look at the problem. Rendering it with [GraphViz](https://graphviz.org/) is probably a good place to start:

```rust
impl<'input> Graph<'input> {
    fn wire_to_graphviz(&self, wire: &str) -> Vec<String> {
        match self.wires[wire] {
            Wire::Input(value) => vec![format!("    {wire} [label=\"{wire}={value}\"];")],
            Wire::Function(op, arg0, arg1) => vec![
                format!("    {wire} [label=\"{wire}={op:?}\"];"),
                format!("    {wire} -> {arg0};"),
                format!("    {wire} -> {arg1};"),
            ],
        }
    }

    pub fn to_graphviz(&self) -> String {
        self.to_graphviz_limited(45)
    }

    pub fn to_graphviz_limited(&self, limit: usize) -> String {
        let mut dot = String::new();

        dot.push_str("digraph {\n");
        dot.push_str("  compounded=true;\n");
        dot.push_str("  rankdir=LR;\n");

        let mut added = HashSet::new();
        let mut by_output: HashMap<&str, HashSet<&str>> = HashMap::new();

        for output in self
            .wires()
            .filter(|w| w.starts_with('z'))
            .sorted()
            .take(limit)
        {
            let deps = self.depends_on(output);

            for dep in deps {
                if !added.contains(&dep) {
                    added.insert(dep);
                    by_output.entry(output).or_default().insert(dep);
                }
            }
        }

        for (output, deps) in by_output.iter().sorted_by(|a, b| a.0.cmp(b.0)) {
            dot.push_str(&format!(
                "  subgraph cluster_{output} {{\n    label=\"{output}\";\n\n",
                output = output
            ));
            for line in self.wire_to_graphviz(output) {
                dot.push_str(&line);
                dot.push('\n');
            }

            for dep in deps.iter().sorted() {
                for line in self.wire_to_graphviz(dep) {
                    dot.push_str(&line);
                    dot.push('\n');
                }
                dot.push('\n');
            }
            dot.push_str("  }\n");
        }

        dot.push_str("}\n");

        dot
    }
}
```

That's a lot of code to render out a `.dot` file that GraphViz can then render. 

```text
digraph {
  compounded=true;
  rankdir=LR;
  subgraph cluster_z00 {
    label="z00";

    z00 [label="z00=Xor"];
    z00 -> y00;
    z00 -> x00;
    x00 [label="x00=true"];

    y00 [label="y00=true"];

    z00 [label="z00=Xor"];
    z00 -> y00;
    z00 -> x00;

  }
  // ...
}
```

If you're just looking at the first 7 output bits, we have:

{{<figure src="/embeds/2024/aoc/day24-limit7.png">}}

... right. We were even told that we were implementing a ripple carry adder. Looking even at this picture, we can see that each block currently does / should look exactly the same (examples from `z03`): 

* Two `AND`s based on the previous block:
  * `cdr` which is the `carry` ripple carry
  * `hjh` which is the `carry` from the input
  * These are `OR` together: `vmr`
* An `XOR` of our bits: `fph`
* A final `XOR` to get the resulting `x03`

Already, we can see a pair of weird ones around `z05` / `z06`. The former is too small (and an `AND` instead of an `XOR`), so that's almost certainly the first of the problems. Scanning through the large image (below), `z11` / `z12` jumps out as another. The other two are sneakier, I did see a swapped `AND`/`XOR` in `z38`/`z39`, but that was more luck than anything. 

Let's see if we can work with this though...

In case you're curious, here's the entire thing as a giant SVG:

{{<figure src="/embeds/2024/aoc/day24-limit45.svg">}}

One other thing we know is that changes have to be local. If they were from radically different parts of the circuit, you'd end up with 

{{<figure src="/embeds/2024/aoc/day24-limit45-wrong.svg">}}

This swaps `njs` and `nwb` and you can see it. 

### Actually solving it

Okay, we know that that it's supposed to be a ripple carry adder and we know what each block is supposed to look like--plus that there are no huge swaps. 

So what we need to is basically go through each bit, build what the structure should be, and check that we have that!

```rust
#[aoc(day24, part2, findadder)]
fn part2_findadder(input: &str) -> String {
    let machine = Machine::from(input);
    let bits = machine.wires().filter(|w| w.starts_with('x')).count();

    fn find_op<'input>(
        machine: &'input Machine,
        op: Operator,
        input1: Option<&'input str>,
        input2: Option<&'input str>,
    ) -> Option<&'input str> {
        if input1.is_none() || input2.is_none() {
            return None;
        }

        for (&output, &wire) in machine.wires.iter() {
            if let Wire::Function(found_op, found_input1, found_input2) = wire {
                if found_op == op
                    && ((found_input1 == input1.unwrap() && found_input2 == input2.unwrap())
                        || (found_input1 == input2.unwrap() && found_input2 == input1.unwrap()))
                {
                    return Some(output);
                }
            }
        }

        None
    }

    let mut carry = None;
    let mut swaps = vec![];

    for bit in 0..bits {
        // New bits we're adding in
        let xin = Some(machine.wire_name(&format!("x{:02}", bit)));
        let yin = Some(machine.wire_name(&format!("y{:02}", bit)));

        // The combinations of just those bits
        let mut adder = find_op(&machine, Operator::Xor, xin, yin);
        let mut next = find_op(&machine, Operator::And, xin, yin);

        // Output should end up being zN and next_carry is the only value passed on
        let mut output = None;
        let mut next_carry = None;

        // Every bit after the first one :smile:
        if carry.is_some() {
            let mut result = find_op(&machine, Operator::And, adder, carry);
            if result.is_none() {
                swaps.push((adder, next));
                std::mem::swap(&mut adder, &mut next);

                result = find_op(&machine, Operator::And, adder, carry);
            }

            // This should be zN
            output = find_op(&machine, Operator::Xor, adder, carry);

            // Check if any of the wires are actually the z bit and swap them
            if adder.is_some_and(|a| a.starts_with('z')) {
                swaps.push((adder, output));
                std::mem::swap(&mut adder, &mut output);
            }

            if next.is_some_and(|a| a.starts_with('z')) {
                swaps.push((next, output));
                std::mem::swap(&mut next, &mut output);
            }

            if result.is_some_and(|a| a.starts_with('z')) {
                swaps.push((result, output));
                std::mem::swap(&mut result, &mut output);
            }

            // Calculate what our next carry will be
            next_carry = find_op(&machine, Operator::Or, next, result);
        }

        // As long as we're not the end, check if the output and carry are swapped
        if bit != (bits - 1) && next_carry.is_some_and(|a| a.starts_with('z')) {
            swaps.push((next_carry, output));
            std::mem::swap(&mut next_carry, &mut output);
        }

        // Pass along the carry to the next chunk of the adder
        carry = if carry.is_some() { next_carry } else { next };
    }

    swaps
        .iter()
        .flat_map(|(a, b)| vec![a.unwrap(), b.unwrap()])
        .sorted()
        .join(",")
}
```

That... is quite a bit of code. I'm honestly as surprised as you are that the first time I ran it:

```bash
$ cargo aoc --day 24 --part 2

AOC 2024
Day 24 - Part 2 - findadder : cgh,frt,pmd,sps,tst,z05,z11,z23
	generator: 583ns,
	runner: 578.459µs
```

Woot. 

## Benchmarks

```bash
$ cargo aoc bench --day 24

Day24 - Part1/v1        time:   [158.71 µs 159.53 µs 160.51 µs]
Day24 - Part2/findadder time:   [229.35 µs 230.37 µs 231.53 µs]
```