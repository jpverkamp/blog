---
title: "AoC 2024 Day 17: Virtual Machininator"
date: 2024-12-17 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Virtual machine
- Shift operations
- Quines
- Bitwise operations
- Backtracking
- Recursion
---
## Source: [Day 17: Chronospatial Computer](https://adventofcode.com/2024/day/17)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day17.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Implement a virtual machine. The machine will have 3 unbounded signed registers, 8 opcodes (see below), a variable parameter scheme (see below that). You will be given the initial values of the 3 registers and a program. Find the final output. 

### Instructions

| Opcode | Instruction   | Description                 | Notes                             |
| ------ | ------------- | --------------------------- | --------------------------------- |
| 0      | `adv reg/val` | `A = A >> OP`               |                                   |
| 1      | `bxl val`     | `B = B ^ OP`                |                                   |
| 2      | `bst reg/val` | `B = OP & 0b111`            |                                   |
| 3      | `jnz val`     | If `a =/= 0`, jump to `LIT` |                                   |
| 4      | `bxc ignore`  | `B = B ^ C`                 | Still takes param, but ignores it |
| 5      | `out reg/val` | Output `b`                  | Only outputs lowest 3 bits        |
| 6      | `bdv reg/val` | `B = A >> OP`               | Same as `adv` but writes to `b`   |
| 7      | `cdv reg/val` | `C = A >> OP`               | Same as `adv` but writes to `c`   |

### Parameter specification

For instructions that can take `reg/val`, `0` to `3` (inclusive) are treated as literal values, `4` is register `A`, `5` is `B`, `6`, is `C`, and `7` is an error (should never happen). 

For instructions that only take `val`, it's always a literal value in the range `0` to `7` (inclusive). 

<!--more-->

I do love [virtual machines](/programming/topics/virtual-machines). 

Here's a representation of the instructions, parameters, and the virtual machine itself:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Instruction {
    Adv,
    Bxl,
    Bst,
    Jnz,
    Bxc,
    Out,
    Bdv,
    Cdv,
}

impl From<u8> for Instruction {
    fn from(value: u8) -> Self {
        match value {
            0 => Self::Adv,
            1 => Self::Bxl,
            2 => Self::Bst,
            3 => Self::Jnz,
            4 => Self::Bxc,
            5 => Self::Out,
            6 => Self::Bdv,
            7 => Self::Cdv,
            _ => panic!("Invalid instruction"),
        }
    }
}

impl fmt::Display for Instruction {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl Instruction {
    // True if the operand is always a literal value, false if it's a combo operand (below)
    fn is_literally_literal(&self) -> bool {
        match self {
            Self::Adv => false,
            Self::Bxl => true,
            Self::Bst => false,
            Self::Jnz => true,
            Self::Bxc => true, // Takes one but ignores it
            Self::Out => false,
            Self::Bdv => false,
            Self::Cdv => false,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Operand {
    Literal(u8),
    A,
    B,
    C,
}

impl From<u8> for Operand {
    fn from(value: u8) -> Self {
        match value {
            0..=3 => Self::Literal(value),
            4 => Self::A,
            5 => Self::B,
            6 => Self::C,
            _ => panic!("Invalid combo operand"),
        }
    }
}

impl fmt::Display for Operand {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Self::Literal(value) => write!(f, "{}", value),
            Self::A => write!(f, "A"),
            Self::B => write!(f, "B"),
            Self::C => write!(f, "C"),
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct Machine {
    pub a: u128,
    pub b: u128,
    pub c: u128,
    pub ip: usize,
    pub ram: Vec<u8>,
    pub halted: bool,
    pub output: Vec<u8>,
}

impl Machine {
    pub fn decompile(&self) -> String {
        let mut output = String::new();

        for (i, &byte) in self.ram.iter().enumerate().step_by(2) {
            let instruction = Instruction::from(byte);
            let operand = if instruction.is_literally_literal() {
                Operand::Literal(self.ram[i + 1])
            } else {
                Operand::from(self.ram[i + 1])
            };

            output.push_str(&format!("{instruction} {operand}\n"));
        }

        output
    }
}
```

Most of that should be a direct translation of the specification, although I do have a few extra fields on the machine:

* `ip` is the [[wiki:instruction pointer]](); the current instruction to decode
* `ram` is the program to run; technically I suppose it should be [[wiki:read-only memory|ROM]]() since you can never actually write to it
* `halted` means the machine has stopped running, this happens whenever `ip` runs past the `ram`
* `output` is a vector of values that have been written by the `out` instructions

To load a machine, we have this wonderfully ugly bit of code:

```rust
#[aoc_generator(day17)]
pub fn parse(input: &str) -> Machine {
    let mut lines = input.lines();
    let a = lines.next().unwrap().rsplit_once(" ").unwrap().1.parse().unwrap();
    let b = lines.next().unwrap().rsplit_once(" ").unwrap().1.parse().unwrap();
    let c = lines.next().unwrap().rsplit_once(" ").unwrap().1.parse().unwrap();

    lines.next(); // Skip the empty line

    let ram = lines
        .next()
        .unwrap()
        .rsplit_once(" ")
        .unwrap()
        .1
        .split(",")
        .map(|s| s.parse().unwrap())
        .collect();

    Machine {
        a,
        b,
        c,
        ip: 0,
        ram,
        halted: false,
        output: Vec::new(),
    }
}
```

... I probably should have written that with `nom` or the like. It's functional though. 

And finally, the actual interpreter itself!

```rust
impl Machine {
    fn value_of(&self, operand: Operand) -> u128 {
        match operand {
            Operand::Literal(value) => value as u128,
            Operand::A => self.a,
            Operand::B => self.b,
            Operand::C => self.c,
        }
    }

    pub fn run(&mut self) {
        while !self.halted {
            self.step();
        }
    }

    pub fn step(&mut self) {
        if self.halted {
            return;
        }

        // Always read an instruction + operand, out of bounds is an error
        if self.ip >= self.ram.len() - 1 {
            self.halted = true;
            return;
        }

        let instruction = Instruction::from(self.ram[self.ip]);
        let operand = if instruction.is_literally_literal() {
            Operand::Literal(self.ram[self.ip + 1])
        } else {
            Operand::from(self.ram[self.ip + 1])
        };

        match instruction {
            // Division (actually a right shift)
            Instruction::Adv => {
                self.a >>= self.value_of(operand);
            }
            // Bitwise XOR
            Instruction::Bxl => {
                self.b ^= self.value_of(operand);
            }
            // Bitwise set
            Instruction::Bst => {
                self.b = self.value_of(operand) & 0b111;
            }
            // Jump (if not zero)
            Instruction::Jnz => {
                if self.a != 0 {
                    self.ip = self.value_of(operand) as usize;
                    return; // Don't increment the IP
                }
            }
            // Bitwise XOR between b and c (ignores operand)
            Instruction::Bxc => {
                self.b ^= self.c;
            }
            // Output
            Instruction::Out => {
                self.output.push((self.value_of(operand) as u8) & 0b111);
            }
            // Division (actually a right shift) to b, still reads from a
            Instruction::Bdv => {
                self.b = self.a >> self.value_of(operand);
            }
            // Division (actually a right shift) to c, still reads from a
            Instruction::Cdv => {
                self.c = self.a >> self.value_of(operand);
            }
        }

        self.ip += 2;
    }
}
```

`value_of` takes either a literal and returns it or a register and returns the value of the register, so any instruction, it will be the operand. Choosing if it's treated as a `literal` or `combo` type operand is handled in `step`.

`step` will advance the machine exactly one step. `run` will run the machine until it `halts`. And hopefully doesn't [[wiki:halt and catch fire|catch fire]](). 

And that's it!

```rust
#[aoc(day17, part1, v1)]
fn part1_v1(input: &Machine) -> String {
    let mut machine = input.clone();

    machine.run();

    machine
        .output
        .iter()
        .map(|b| b.to_string())
        .collect::<Vec<_>>()
        .join(",")
}
```

... it took me longer than I care to admit to realize that I needed to include the `,` in the output this time around. 

### Unit tests

I actually did write some tests for each operation (based on comments in the Advent of Code specification):

```rust
#[cfg(test)]
mod tests {
    // If register C contains 9, the program 2,6 would set register B to 1.
    #[test]
    fn test_instruction_1() {
        let mut machine = Machine::default();
        machine.c = 9;
        machine.ram = vec![2, 6];

        machine.step();

        assert_eq!(machine.b, 1);
    }

    // If register A contains 10, the program 5,0,5,1,5,4 would output 0,1,2.
    #[test]
    fn test_instruction_2() {
        let mut machine = Machine::default();
        machine.a = 10;
        machine.ram = vec![5, 0, 5, 1, 5, 4];

        machine.step();
        machine.step();
        machine.step();

        assert_eq!(machine.output, vec![0, 1, 2]);
    }

    // If register A contains 2024, the program 0,1,5,4,3,0 would output 4,2,5,6,7,7,7,7,3,1,0 and leave 0 in register A.
    #[test]
    fn test_instruction_3() {
        let mut machine = Machine::default();
        machine.a = 2024;
        machine.ram = vec![0, 1, 5, 4, 3, 0];

        while !machine.halted {
            machine.step();
        }

        assert_eq!(machine.output, vec![4, 2, 5, 6, 7, 7, 7, 7, 3, 1, 0]);
        assert_eq!(machine.a, 0);
    }

    // If register B contains 29, the program 1,7 would set register B to 26.
    #[test]
    fn test_instruction_4() {
        let mut machine = Machine::default();
        machine.b = 29;
        machine.ram = vec![1, 7];

        machine.step();

        assert_eq!(machine.b, 26);
    }

    // If register B contains 2024 and register C contains 43690, the program 4,0 would set register B to 44354.
    #[test]
    fn test_instruction_5() {
        let mut machine = Machine::default();
        machine.b = 2024;
        machine.c = 43690;
        machine.ram = vec![4, 0];

        machine.step();

        assert_eq!(machine.b, 44354);
    }
}
```

I'll admit, I threw an LLM at those. It did perfectly at turning the plain text specification into test cases after I wrote the first one. And the one it did mess up... that was actually a problem they found in my implementation!

## Part 2

> Find the initial value of `a` so that your program outputs it's own code. 

Make a [[wiki:quine]]()!

Let's brute force it:

```rust
#[aoc(day17, part2, bruteforce)]
fn part2_bruteforce(input: &Machine) -> u128 {
    for a in (8 ^ 15).. {
        let mut machine = input.clone();
        machine.a = a;
        machine.run();
        if machine.output == machine.ram {
            return a;
        }
    }

    panic!("No solution found");
}
```

...

... ...

What's that even outputting? 

```bash
$ cargo run --bin day17-iterator | head -n 1000

Input A    Octal      Output
0          0          [2]
1          1          [3]
2          2          [0]
3          3          [1]
4          4          [7]
5          5          [7]
6          6          [2]
7          7          [6]
8          10         [2, 3]
9          11         [3, 3]
10         12         [0, 3]
11         13         [1, 3]
12         14         [5, 3]
13         15         [6, 3]
14         16         [2, 3]
15         17         [2, 3]
16         20         [2, 0]
17         21         [3, 0]
18         22         [1, 0]
19         23         [1, 0]
# ...
62         76         [2, 6]
63         77         [2, 6]
64         100        [3, 2, 3]
65         101        [3, 2, 3]
66         102        [4, 2, 3]
67         103        [3, 2, 3]
68         104        [7, 2, 3]
# ...
510        776        [2, 2, 6]
511        777        [2, 2, 6]
512        1000       [2, 3, 2, 3]
513        1001       [7, 3, 2, 3]
514        1002       [0, 3, 2, 3]
515        1003       [1, 3, 2, 3]
# ...
```

Okay, so if we treat the input `a` as an [[wiki:octal]]() value (which makes sense, since everything is working with 3 bits), then each time we add another octet to the input... we get another octet of output. So if we need all 16 octets of output, our input needs to be... 16 octets = 48 bits long. That's... 281 trillion! Even for a really fast computer... that might take a while. 

I did some quick timing and showed that without much more optimization, we're running at ~4 MHz (4 million values per second). Since the value we're looking for is ~ $8^16$, we'd need... about 800 days to find the answer. Even if we start at $8^15$ instead of $1$... that only cuts off ~100 days. 

It's like the saying says: what's the difference between $1 million and $1 billion? About $1 billion. 

Anyways. 

Let's be smarter about this. 

### So what is our program actually doing? 

I already wrote a `decompile` method, let's see what the program is doing:

```text
Bst A
Bxl 6
Cdv B
Bxc 6
Bxl 4
Out B
Adv 3
Jnz 0
```

Well that's helpful. :smile:

To translate a bit more, we have:

```text
Bst A   B0 = A{N}           Truncated to 3 bits
Bxl 6   B1 = A{N} ^ 110
Cdv B   C0 = A{N} >> B1     C0 = A{N + B1}
Bxc 6   B2 = C0 ^ B1
Bxl 4   B = B ^ [0 1 1]
Out B   output B            Truncated to 3 bits
Adv 3   A = A{N+3}
Jnz 0   loop
```

I'm using `A{N}` to represent the bits of `A` starting from the `N`th [[wiki:least significant bit]](). I'm using `B0`/`B1`/`B2` to put this in [[wiki:static single-assignment]]() form (and so it's easier to tell which B is which). 

### Psuedo-code hash

So essentially, we have code that does this:

```text
while A > 0 {
    output A{N} ^ A{N + ?} ^ some_literal_bytes
    A = A >>> 3
}
```

Basically it's a [[wiki:hashing function]](). Although not a great one...

The interesting part is that `A{N + ?}`. Because `B1` is based on `B0` which is truncated, we know that the `?` is at most `7`. So at most, each output value is based on the three bits directly above it + up to 7 more. 

This is probably interesting. :smile:

### What's actually changing? 

As an aside, I did do a quick visualization of this, starting with the program (converted as octal) as the input to `A` then I tried changing each `tribble` (3 bit nibble?) and showing which octets of the output changed:

```rust
fn decimalize(ram: &[u8]) -> u128 {
    let mut a = 0;
    for nibble in ram.iter() {
        a = (a << 3) | (*nibble as u128);
    }
    a
}

let mut a = input.ram.clone();
let mut change_map = Grid::new(input.ram.len(), input.ram.len());

// Which bytes change which bytes
for index in 0..input.ram.len() {
    let mut machine = input.clone();
    machine.a = decimalize(&a);
    machine.run();
    let output_1 = machine.output.clone();

    for new_value in 0..8 {
        let mut machine = input.clone();
        a[index] = new_value;
        machine.a = decimalize(&a);
        machine.run();
        let output_2 = machine.output.clone();

        output_1
            .iter()
            .zip(output_2.iter())
            .enumerate()
            .filter(|(_, (a, b))| a != b)
            .for_each(|(i, _)| {
                change_map.set((index, i), true);
            });
    }
}

println!(
    "{}",
    change_map.to_string(&|b| (if *b { 'X' } else { '.' }).to_string())
);
```

This outputs this fun looking chart:

```text
.............X.X
............XXX.
...........XXX..
..........X.X...
..........XX....
.........XX.....
........XX......
.....XX.X.......
.......X........
.....XX.........
....XX..........
...XX...........
...X............
X.X.............
XX..............
X...............
```

Which shows pretty much exactly what I expected: each octet is based on up to a set of 4 above it. 

### Zero guarantees

So what else do we know? 

Well, we know that in the final loop, we have `A{N} = 0`. And from there, for each octet, we should be able to try each different octet (`0` to `7`) as input. Some subset of those should output the next correct value--and if we continue down this line, only some of *those* should still be valid. Eventually, we run out of characters to generate in our [[wiki:quine]](). 

That sounds an awful lot like [[wiki:recursion]](). 

### The actual answer

```rust
#[aoc(day17, part2, backtrack)]
fn part2_backtrack(input: &Machine) -> u128 {
    fn recur(original_machine: &Machine, a: u128, index: usize) -> Option<u128> {
        for tribble in 0..8 {
            let mut machine = original_machine.clone();
            let next_a = (a << 3) | tribble;
            machine.a = next_a;
            machine.run();

            if machine.output[0] == machine.ram[index] {
                // Recursive base case
                if index == 0 {
                    return Some(next_a);
                }

                if let Some(a) = recur(original_machine, next_a, index - 1) {
                    return Some(a);
                }
            }
        }

        None
    }

    recur(input, 0, input.ram.len() - 1).unwrap()
}
```

At each `recur`sive step, we assume we have `a` that is correct up until `index` of the target string. Try each next `tribble` (octet), recurring down on the next `index` for each. If any of those returns a value, that's also the final answer. If none do, this branch doesn't have the answer, so backtrack (by the power of recursion!) and try another value somewhere earlier in the program. 

That's... amazingly simple. 

```bash
$ cargo aoc --day 17 --part 1

AOC 2024
Day 17 - Part 2 - backtrack : 90938893795561
	generator: 709ns,
	runner: 45.041µs
```

And $\frac{log{(90938893795561)}}{log{(8)}} \approx 15.45$, so exactly the 16 octets long we were expecting!

In case you were wondering, you can print out the values of `a` and `index` to see how many different branches we actually end up needing to try:

```text
recur 0 15
recur 2 14
recur 17 13
recur 20 13
recur 165 12
recur 1323 11
recur 10586 10
recur 84690 9
recur 84693 9
recur 677547 8
recur 5420377 7
recur 43363017 6
recur 346904138 5
recur 2775233106 4
recur 2775233109 4
recur 43363021 6
recur 5420380 7
recur 43363041 6
recur 43363042 6
recur 43363043 6
recur 346904349 5
recur 2775234796 4
recur 22201878368 3
recur 177615026944 2
recur 1420920215555 1
recur 11367361724445 0
```

26! (No, not [that 26!](https://www.wolframalpha.com/input?i=26%21)). 

That's it. 

And while it doesn't generalize to any possible program, since we can only right shift and xor, most programs should be similarly impacted. 

## Benchmarks

```bash
$ cargo aoc bench --day 17

Day17 - Part1/v1        time:   [465.51 ns 469.71 ns 474.07 ns]
Day17 - Part2/backtrack time:   [43.640 µs 43.798 µs 43.951 µs]
```
