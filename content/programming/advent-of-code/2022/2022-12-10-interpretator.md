---
title: "AoC 2022 Day 10: Interpretator"
date: 2022-12-10 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Graphics
- Cellular Automata
- Retro Graphs
---
## Source: [Cathode-Ray Tube](https://adventofcode.com/2022/day/10)

## Part 1

> Implement a simple virtual machine with two instructions: `nop` which does nothing for 1 cycles and `addx $n` which adds `$n` to the `X` register (initial value 1) in two cycles. Calculate the sum of `cycle * X` for the cycles 20, 60, 100, 140, 180, 220. 

<!--more-->

I do love virtual machines. 

First, parse and store the instructions:

```rust
/* ----- A single instruction for the virtual machine ----- */
#[derive(Copy, Clone, Debug)]
enum Instruction {
    Noop,
    AddX(isize),
}

impl Instruction {
    fn cycles(self) -> usize {
        match self {
            Noop => 1,
            AddX(_) => 2,
        }
    }
}

impl From<String> for Instruction {
    fn from(line: String) -> Self {
        let mut parts = line.split_ascii_whitespace();

        match parts.next().expect("must have a first part") {
            "noop" => Noop,
            "addx" => {
                let v = parts
                    .next()
                    .expect("addx must have a value")
                    .parse::<isize>()
                    .expect("addx value must be numeric");

                AddX(v)
            }
            _ => panic!("unknown instruction format {:?}", line),
        }
    }
}
```

Second, create the struct for the `VM`:

```rust
/* ----- Implement a simple virtual machine ----- */
#[derive(Debug)]
struct VM {
    instructions: Vec<Instruction>,
    program_counter: usize,
    time_counter: usize,
    delayed_instructions: VecDeque<Vec<Instruction>>,
    registers: HashMap<String, isize>,
    previous_registers: HashMap<String, isize>,
}

impl VM {
    fn new(instructions: Vec<Instruction>) -> Self {
        VM {
            instructions,
            program_counter: 0,
            time_counter: 0,
            delayed_instructions: VecDeque::new(),
            registers: HashMap::new(),
            previous_registers: HashMap::new(),
        }
    }
}
```

The fields probably need a bit of talking about:

* `instructions` stores the full program
* `program_counter` is the current instruction being executed
* `time_counter` advances one for each tick 
* `delayed_instructions` is a stack of instructions that are waiting to be executed; this is structured a bit oddly, since originally I read the prompt wrong and implemented an (IMO) more interesting architecture, one with {{<wikipedia "instruction pipelining">}}--essentially, an `addx` followed by a `nop` would finish both on the same clock cycle; mostly it messed up the timing
* `registers` stores the current value of registers, this could just be a single value since we only use `X`, but :shrug:
* `previous_registers` stores the values the registers had on the tick before this one, since that's the value 'during' the current cycle (which is what part 1 actually wants) while `registers` is what it is after the cycle; again, I could just offset the `time_counter`, but I think this is more explicit

Okay, with all that, let's write the function that actually updates the `VM`:

```rust
impl VM {
    fn step(&mut self) {
        self.time_counter += 1;

        match self.delayed_instructions.get(0) {
            // We have a current instruction, don't queue any more
            Some(v) if !v.is_empty() => {}

            // We don't have a current instruction, queue one
            _ => {
                let instruction = self.instructions.get(self.program_counter).unwrap();
                let cycles = instruction.cycles();

                while self.delayed_instructions.len() < cycles {
                    self.delayed_instructions.push_back(Vec::new());
                }

                self.delayed_instructions
                    .get_mut(cycles - 1)
                    .unwrap()
                    .push(*instruction);

                self.program_counter += 1;
            }
        }

        // Copy the registers
        for (k, v) in self.registers.iter() {
            self.previous_registers.insert(k.clone(), *v);
        }

        // Run any current instructions
        for instructions in self.delayed_instructions.pop_front() {
            for instruction in instructions {
                self.eval(instruction);
            }
        }
    }
}
```

As noted, I'm using `delayed_instructions` to handle the offset of various ticks. In this case, when an instruction executes, it's added to `delayed_instructions` offset by the number of cycles it will take to finish. So `nop` will end up at the `front` of the `VecDeque` (and thus will be executed this cycle) and `addx` will be added a cycle further down. 

This is (as I tend to do) rather overengineered. You could easily add both many instructions and already do some pipelining, although with this `step` function, it will never matter (since the next instruction is only queued if there isn't one ready to run). 

Since I think it's cool, here is the pipelined step function:

```rust
impl VM {
        #[allow(dead_code)]
    fn pipelined_step(&mut self) {
        // Add the current instruction to the correct delay cycle
        if self.program_counter < self.instructions.len() {
            let instruction = self.instructions.get(self.program_counter).unwrap();
            let cycles = instruction.cycles();

            while self.delayed_instructions.len() < cycles + 1 {
                self.delayed_instructions.push_back(Vec::new());
            }

            self.delayed_instructions
                .get_mut(cycles)
                .unwrap()
                .push(*instruction);
        }

        // Copy the registers
        for (k, v) in self.registers.iter() {
            self.previous_registers.insert(k.clone(), *v);
        }

        // Pop and run all currently delay instructions
        for instructions in self.delayed_instructions.pop_front() {
            for instruction in instructions {
                self.eval(instruction);
            }
        }

        // Increment program counter
        self.program_counter += 1;
    }
}
```

Again, overengineered, but this time much more interesting. If you have some very long instructions, it can properly start each one cycle at a time and they'll finish when they finish. This of course doesn't take into account problems with data access etc that actual pipelined architectures handle, but rather assumes that the programmer will add the proper number of `nop` instructions and/or move code around so that it isn't a problem. 

I thought it was neat. :smile:

In any case, we do need two more functions, one to tell the user when the VM is done (in this case, the `program_counter` is out of bounds and all `delayed_instructions` are completed) plus an actual `eval` function for all currently defined instructions:

```rust
impl VM {
    fn is_finished(&self) -> bool {
        self.program_counter >= self.instructions.len() && self.delayed_instructions.is_empty()
    }

    fn eval(&mut self, instruction: Instruction) {
        match instruction {
            Noop => {}
            AddX(v) => {
                self.registers.insert(
                    String::from("X"),
                    self.registers.get("X").or(Some(&(1 as isize))).unwrap() + v,
                );
            }
        }
    }
}
```

The `.get("X").or(Some(&1))` is pretty cool, not going to lie. The ability to default is always neat. 

In any case, now that we have the VM, the next step is to use it to solve the requested problem:

```rust
fn part1(filename: &Path) -> String {
    let instructions = iter_lines(filename).map(Instruction::from).collect();
    let mut vm = VM::new(instructions);

    let mut sample_sum = 0;

    loop {
        vm.step();

        if cfg!(debug_assertions) {
            println!(
                "[{:4}] [{:4}] {:?}, {:?}",
                vm.time_counter, vm.program_counter, vm.registers, vm.delayed_instructions
            );
        }

        match vm.time_counter {
            20 | 60 | 100 | 140 | 180 | 220 => {
                let signal = vm.time_counter as isize * *vm.previous_registers.get("X").unwrap();
                sample_sum += signal;
            }
            _ => {}
        }

        if vm.is_finished() {
            break;
        }
    }

    sample_sum.to_string()
}
```

And it even has the `debug_assertions` code to print out the current state of the VM at each tick! 

## Part 2

> Simulate an old fashioned monitor that works by displaying one bit at a time, across each row and then down to the next row. Each tick, display a `#` if the current value of the `X` register is +-1 the current bit being displayed, otherwise, `.`. 

Check out {{<wikipedia "racing the beam">}}. It's something that you could do to really get some extra performance out of the *old* video game systems. Not so much an issue with modern computers. Fascinating what different trade offs have been made over the years. 

In any case, the `VM` will handle this absolutely perfectly, so let's go ahead and modify `part2` to instead generate an `output_buffer` for one frame:

```rust
fn part2(filename: &Path) -> String {
    let instructions = iter_lines(filename).map(Instruction::from).collect();
    let mut vm = VM::new(instructions);

    let mut output_buffer = String::new();
    let mut crt_x = 0;

    loop {
        vm.step();

        let sprite_center_x = *vm.previous_registers.get("X").or(Some(&1)).unwrap();
        let c = if crt_x >= sprite_center_x - 1 && crt_x <= sprite_center_x + 1 {
            '#'
        } else {
            '.'
        };

        output_buffer.push(c);

        crt_x += 1;
        if crt_x >= 40 {
            output_buffer.push('\n');
            crt_x = 0;
        }

        if vm.is_finished() {
            break;
        }
    }

    output_buffer.to_string()
}
```

That's a pretty neat function and I think easy enough to understand. It does hardcode the sprite as a 3px wide block, but so it goes. 

## Performance

```bash
$ ./target/release/10-interpretator 1 data/10.txt

15140
took 201.791µs

$ ./target/release/10-interpretator 2 data/10.txt

###..###....##..##..####..##...##..###..
#..#.#..#....#.#..#....#.#..#.#..#.#..#.
###..#..#....#.#..#...#..#....#..#.#..#.
#..#.###.....#.####..#...#.##.####.###..
#..#.#....#..#.#..#.#....#..#.#..#.#....
###..#.....##..#..#.####..###.#..#.#....

took 481.583µs
```

Yeah, that's pretty cool. And it's actually still *well* under the ~16.67ms you need to be able to render a frame in to get 60fps. Granted, it's not *doing* anything and without any branching, it's not really capable of doing anything interesting (read: {{<wikipedia "Turing complete">}}). But it's a start! I'm curious if a later day will go there. 

In any case, onward!