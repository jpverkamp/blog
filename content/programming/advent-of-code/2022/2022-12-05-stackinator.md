---
title: "AoC 2022 Day 5: Stackinator"
date: 2022-12-05 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Supply Stacks](https://adventofcode.com/2022/day/5)

#### **Part 1:** Given a list of stacks of *syntax 1* and instructions in the form *syntax 2*, apply each instruction to pop `qty` items from the stack `src` and put them on `dst` one at a time. 

```text
Syntax 1: Stacks

    [D]    
[N] [C]    
[Z] [M] [P]
 1   2   3 

Syntax 2: Instructions

move 1 from 2 to 1
move 3 from 1 to 3
move 2 from 2 to 1
move 1 from 1 to 2
```

<!--more-->

Well that's an interesting format. I expect most of this problem is going to resolve around parsing rather than the actual mechanics of the problem itself. So let's start with structs for `Stack`, a `Warehouse` to hold all of the stacks, and `Instructions`. We could certainly just use `Vec<Vec<char>>` as our `Stack`/`Warehouse`, but I like being able to attach functionality to the structs with `impl`. To each their own. 

```rust
#[derive(Debug)]
struct Stack {
    data: Vec<char>,
}

#[derive(Debug)]
struct Warehouse {
    stacks: Vec<Stack>,
}

#[derive(Debug)]
struct Instruction {
    qty: usize,
    src: usize,
    dst: usize,
}
```

Next, parse a warehouse, assuming that we're only given the lines containing the boxes (as above). 

```rust
impl Warehouse {
    fn from(lines: &Vec<String>) -> Warehouse {
        let mut data = Vec::new();

        for line in lines {
            for i in 0..=(line.len() / 3) {
                let center = 1 + i * 4;
                let c = line.chars().nth(center);

                match c {
                    Some(c) if c != ' ' => {
                        while data.len() <= i {
                            data.push( Vec::new() );
                        }

                        data[i].push(c);
                    }
                    _ => {} // No box in this stack, do nothing
                }
            }
        }

        let mut stacks = Vec::new();
        for ls in data {
            stacks.push(Stack { data: ls.into_iter().rev().collect::<Vec<char>>() });
        }

        Warehouse { stacks }
    }
```

To do this, I'm going to actually build up that `Vec<Vec<char>>` and convert it at the end. But that ends up being an implementation detail so far as anyone viewing this code would be considered. The `from` method would be `pub`, but the struct fields do not have to be. 

A few interesting things to note:

* The `i in 0..=(line.len() / 3)` iterates across indexes within each string length, so you only loop to the rightmost *existing* char in each row
* The `match` block deals with blocks that don't exist both by unwrapping the `nth` and checking `if c != ' '`
* The `mut stacks` loop at the bottom is because we read each stack top to bottom, but want them stored with the top value at the end (`Vec`s are {{<inline-latex "O(1)">}} from that end), so reverse them once here

Now that we have all of that, we also want the ability to parse out a `Vec<Instruction>`:

```rust
impl Instruction {
    fn list_from(lines: &Vec<String>) -> Vec<Instruction> {
        let mut result = Vec::new();

        for line in lines {
            let mut parts = line.split_ascii_whitespace();
            
            // Note: nth consumes previous values
            let qty = parts.nth(1).expect("part 2 is qty").parse::<usize>().expect("part 2 must be a uint");
            let src = parts.nth(1).expect("part 4 is src").parse::<usize>().expect("part 4 must be a uint");
            let dst = parts.nth(1).expect("part 6 is dst").parse::<usize>().expect("part 6 must be a uint");

            result.push(Instruction{ qty, src, dst });
        }

        result
    }
}
```

It took a bit to remember/notice that `nth` on an `Iter` consumes up to and through that value. So `.nth(1)` the first time skips `move` and consumes the number, the second time `from` and the number, and the third time `to` and the number. Pretty neat actually. 

Now finally, a function to `apply` an `Instruction` to a `Warehouse`:

```rust
impl Warehouse {
    fn apply(&mut self, instruction: &Instruction) {
        for _ in 0..instruction.qty {
            let value = self.stacks[instruction.src - 1].data.pop().expect("tried to pop from empty stack");
            self.stacks[instruction.dst - 1].data.push(value);
        }
    }
}
```

And a function to get the final result:

```rust
impl Warehouse {
    fn tops(&self) -> String {
        let mut result = String::new();

        for stack in self.stacks.iter() {
            let c = stack.data.last().expect("each stack should have at least one item");
            result.push(*c);
        }

        result
    }
}
```

Pretty clean. We do need one last bit of boilerplate to be able to split the input based on the two parts (separated by an empty line) though:

```rust
fn parse(filename: &Path) -> (Warehouse, Vec<Instruction>) {
    let mut lines = read_lines(filename);
    let split_index = lines.iter().position(|line| line.len() == 0).expect("should have empty line");
    let instruction_lines = lines.split_off(split_index + 1);
    
    // Ignore the indexes and empty line
    lines.pop();
    lines.pop();

    let warehouse = Warehouse::from(&lines);
    let instructions = Instruction::list_from(&instruction_lines);
    
    (warehouse, instructions)
}
```

Still looking for a better way to do that. I suppose I could use an `Iter<String>` instead, read off values until I see the empty line in the first parser and then read from the same `Iter` in the second? Perhaps I'll try that for another day. 

In any case, all this means that the actual answer is very short (as it should be):

```rust
fn part1(filename: &Path) -> String {
    let (mut warehouse, instructions) = parse(filename);

    for instruction in instructions {
        warehouse.apply(&instruction);
    }

    warehouse.tops()
}
```

Cool!

#### **Part 2:** Do the same, except instead of moving `qty` items one at a time, pick up the entire `qty` items and move them all at once (thus preserving the original order). 

Just need a new apply function:

```rust
impl Warehouse {
    fn apply_9001(&mut self, instruction: &Instruction) {
        let mut values = LinkedList::new();

        for _ in 0..instruction.qty {
            values.push_back(self.stacks[instruction.src - 1].data.pop().expect("tried to pop from empty stack"));
        }

        for _ in 0..instruction.qty {
            self.stacks[instruction.dst - 1].data.push(values.pop_back().expect("must pop as many as we pushed"));
        }
    }
}

fn part2(filename: &Path) -> String {
    let (mut warehouse, instructions) = parse(filename);

    for instruction in instructions {
        warehouse.apply_9001(&instruction);
    }

    warehouse.tops()
}
```

And for this, we actually do want a `LinkedList`, since that allows {{<inline-latex "O(1)" >}} push and pop from both ends, so we can have {{<wikipedia FIFO>}} instead of {{<wikipedia FILO>}}. 

#### Performance

```bash
$ ./target/release/05-stackinator 1 data/05.txt

TLFGBZHCN
took 260.208µs

$ ./target/release/05-stackinator 2 data/05.txt

QRQFHFWCL
took 367.333µs
```

Reading is {{<inline-latex "O(n)">}} in the number of stacks (since it has to read them all in and then flip them all, but that's still not a higher order of magnitude) and running is likewise {{<inline-latex "O(n)">}} in the number of instructions, it doesn't matter how big the actual data is. So it should (as expected) be lightning fast, no matter really how big the problem us (up until you get big enough to start worrying more about memory consumption and caching). 

Pretty neat!