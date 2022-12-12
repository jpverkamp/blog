---
title: "AoC 2022 Day 11: Monkeyinator"
date: 2022-12-11 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Monkey in the Middle](https://adventofcode.com/2022/day/11)

#### **Part 1:** Simulate a collection of 'monkeys'. Each monkey will have a number of items which it will then apply a mathematical operation to, then always divide by 3, then test divisibility to pass to one of two other monkeys. Return as answer the product of the two highest number of times a monkey applies it's main function to individual items after 20 steps. 

Note: Monkeys will always be evaluated in order (so monkey 1 will evaluate any items passed by monkey 0 again in the same round). 

<!--more-->

That note certainly caused me some issues. :D

As always, let's start by creating a `Monkey` struct and parsing the input:

```rust
type BinOp = fn(isize, isize) -> isize;

/* ----- A single monkey with a brain that can hold, throw, and catch items ----- */
#[derive(Debug)]
struct Monkey {
    held: Vec<isize>,
    operation: (BinOp, Option<isize>),
    test_divisor: isize,
    true_friend: usize,
    false_friend: usize,
    inspection_count: usize,
}

impl<I> From<&mut I> for Monkey
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        iter.next()
            .expect("skip name line, assume monkeys are ordered");

        // Read starting items
        let mut line = iter.next().expect("must have starting items");
        let mut parts = line.split_ascii_whitespace().skip(2);
        let mut held = Vec::new();
        for value in parts {
            held.push(
                value
                    .strip_suffix(",")
                    .or(Some(value))
                    .expect("strip/or success")
                    .parse::<isize>()
                    .expect("held items must be numbers"),
            );
        }

        // Read operator
        line = iter.next().expect("must have an operation");
        parts = line.split_ascii_whitespace().skip(4);

        let op: fn(isize, isize) -> isize = match parts.next().expect("must have an operator") {
            "*" => |a, b| a * b,
            "+" => |a, b| a + b,
            _ => panic!("unknown operator in {:?}", line),
        };

        let value = parts
            .next()
            .expect("operation must have a value")
            .parse::<isize>()
            .ok();

        let operation = (op, value);

        // Read test
        let test_divisor = iter
            .next()
            .expect("must have a test line")
            .split_ascii_whitespace()
            .last()
            .expect("test must have at least one elmeent")
            .parse::<isize>()
            .expect("divisor must be a number");

        // Read friends
        let true_friend = iter
            .next()
            .expect("must have true friend")
            .split_ascii_whitespace()
            .last()
            .expect("true friend must have at least one element")
            .parse::<usize>()
            .expect("true friend must be an index");

        let false_friend = iter
            .next()
            .expect("must have false friend")
            .split_ascii_whitespace()
            .last()
            .expect("false friend must have at least one element")
            .parse::<usize>()
            .expect("false friend must be an index");

        Monkey {
            held,
            operation,
            test_divisor,
            true_friend,
            false_friend,
            inspection_count: 0,
        }
    }
}
```

So those are certainly some crazy parsing statements, but I think it works pretty well. Really, it takes in the line iterator and then for each, reads and splits that line, skips the unneeded text, and parses out numbers/functions/whatever we need. 

Next up, the core of the algorithm, the `toss` function. 

```rust
impl Monkey {
    fn toss(&mut self) -> Vec<(usize, isize)> {
        let mut items_in_the_air = Vec::new();

        // For each currently held item
        for old_item in self.held.iter() {
            // Count inspected items
            self.inspection_count += 1;

            // Calculate the new value, None means op is op(old, old)
            let (op, value) = self.operation;
            let mut new_item = op(*old_item, value.or(Some(*old_item)).unwrap());

            // Divide worry by three after each toss
            new_item /= 3;

            // Use the test_divisor to determine which friend we're passing to
            let target = if new_item % self.test_divisor == 0 {
                self.true_friend
            } else {
                self.false_friend
            };

            // Put that in the correct 'in the air' bucket
            items_in_the_air.push((target, new_item));
        }

        // Clear my held items since we just threw them all
        self.held.clear();

        items_in_the_air
    }

    fn catch(&mut self, item: isize) {
        self.held.push(item);
    }
}
```

I think that's a pretty direct interpretation. The main interesting bit is that it will send back a `Vec` of tuples where each tuple has the `(target monkey, new value)`. `catch` is a wrapper just to push items back into held, we'll handle that next. 

Next up, we want to generalize a whole pile of monkeys all at once. A `MonkeyPile` as it were. First, the `struct` and a parser than can handle parsing monkeys and skipping whitespace until the end of the input stream:

```rust
/* ----- A collection of monkeys passing things around ----- */
#[derive(Debug)]
struct MonkeyPile {
    monkeys: Vec<Monkey>,
}

impl<I> From<&mut I> for MonkeyPile
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        let mut iter = iter.peekable();
        let mut monkeys = Vec::new();

        'monkeys: loop {
            monkeys.push(Monkey::from(&mut iter));

            'whitespace: loop {
                match iter.peek() {
                    Some(line) if line.is_empty() => {
                        iter.next();
                    }
                    None => {
                        break 'monkeys;
                    }
                    _ => {
                        break 'whitespace;
                    }
                }
            }
        }

        MonkeyPile { monkeys: monkeys }
    }
}
```

I do think named `break`/`continue` is something more languages should have. In this case, we do also make use of `.peekable()` to look ahead and see if the next line is an empty line (or `None`) without actually consuming it. 

Now, the rest of the algorithm, `step`ping through each `Monkey` in the `MonkeyPile`:

```rust
impl MonkeyPile {
    fn step(&mut self, worry_fix: &MonOp) {
        // Toss all of the items into the air
        for index in 0..self.monkeys.len() {
            let items_in_the_air = self.monkeys.get_mut(index).unwrap().toss(worry_fix);

            for (index, item) in items_in_the_air.into_iter() {
                self.monkeys
                    .get_mut(index)
                    .expect("monkey at index must exist to catch items")
                    .catch(item);
            }
        }
    }
}
```

This one I couldn't quite get right at first, since I really wanted to be able to do `for monkey in self.monkeys`. But I also needed that to be mutable in two different places. Rust (rightfully) doesn't trust that. It actually came to me on a walk (as these things do): iterate over the indexes. 

And it worked!

So now you can `get_mut` once to toss and then Rust knows that that mutable reference goes out of scope (since I don't assign it to a variable) so it's safe to `get_mut` and `catch`. 

I feel like I'm really getting the hang of this thing. I expect I'll be prove wrong in a day or three. 

And that's it! So let's actually solve the problem:

```rust
fn part1(filename: &Path) -> String {
    let mut iter = iter_lines(filename);
    let mut monkey_pile = MonkeyPile::from(&mut iter);

    for _i in 0..20 {
        monkey_pile.step();
    }

    let mut sorted_monkeys = monkey_pile.monkeys.iter().collect::<Vec<_>>();
    sorted_monkeys.sort_by(|m1, m2| m1.inspection_count.cmp(&m2.inspection_count));
    sorted_monkeys.reverse();

    let monkey_business_score = sorted_monkeys[0].inspection_count * sorted_monkeys[1].inspection_count;
    monkey_business_score.to_string()
}
```

Making a copy to `sort_by` is a bit weird, but it works. 

Onward!

#### **Part 2:** Remove the 'divide by 3' requirement and run the simulation for 10,000 steps. 

> Unfortunately, that relief was all that was keeping your worry levels from reaching ridiculous levels. You'll need to find another way to keep your worry levels manageable.
 
Heh. If I were working in Python I would definitely consider just letting it go. It will end up overflowing even `i128` (biiiig numbers). But we can do better. 

Looking through, all of the tests are divisibility. That's the clue to how to solve this problem, since divisibility doesn't change for any number `n` such that `x % n == 0`. We just need that to be true for all possible divisibility values. 

And there is a function exactly for that: {{<wikipedia "least common multiple">}}! 

Unfortunately, although that appears to be (or have been) a function in Rust at one point ([`lcm`](https://docs.rs/num/0.1.32/num/integer/fn.lcm.html)), it isn't in the version I'm using. But ... we don't actually need the *least* common multiple. Any multiple will work. 

So:

```rust
fn part2(filename: &Path) -> String {
    let mut iter = iter_lines(filename);
    let mut monkey_pile = MonkeyPile::from(&mut iter);

    // All tests are divisibility tests, so we only need to word mod(lcm(...))
    // I don't see an LCM function in the stdlib, so this will work (just less efficient)
    let mut worry_value = 1;
    for monkey in monkey_pile.monkeys.iter() {
        worry_value *= monkey.test_divisor;
    }
    let worry_fix = move |v| v % worry_value;

    for _i in 0..10000 {
        monkey_pile.step(&worry_fix);
    }

    let mut sorted_monkeys = monkey_pile.monkeys.iter().collect::<Vec<_>>();
    sorted_monkeys.sort_by(|m1, m2| m1.inspection_count.cmp(&m2.inspection_count));
    sorted_monkeys.reverse();

    let monkey_business_score =
        sorted_monkeys[0].inspection_count * sorted_monkeys[1].inspection_count;
    monkey_business_score.to_string()
}
```

:D 

It works!

I did have to modify the original `step` and `toss` functions though:

```rust
type MonOp = dyn Fn(isize) -> isize;

impl Monkey {
    fn toss(&mut self, worry_fix: &MonOp) -> Vec<(usize, isize)> {
        let mut items_in_the_air = Vec::new();

        // For each currently held item
        for old_item in self.held.iter() {
            // Count inspected items
            self.inspection_count += 1;

            // Calculate the new value, None means op is op(old, old)
            let (op, value) = self.operation;
            let mut new_item = op(*old_item, value.or(Some(*old_item)).unwrap());

            // Apply a function to update worry
            new_item = worry_fix(new_item);

            // Use the test_divisor to determine which friend we're passing to
            let target = if new_item % self.test_divisor == 0 {
                self.true_friend
            } else {
                self.false_friend
            };

            // Put that in the correct 'in the air' bucket
            items_in_the_air.push((target, new_item));
        }

        // Clear my held items since we just threw them all
        self.held.clear();

        items_in_the_air
    }

    fn catch(&mut self, item: isize) {
        self.held.push(item);
    }
}

impl MonkeyPile {
    fn step(&mut self, worry_fix: &MonOp) {
        // Toss all of the items into the air
        for index in 0..self.monkeys.len() {
            let items_in_the_air = self.monkeys.get_mut(index).unwrap().toss(worry_fix);

            for (index, item) in items_in_the_air.into_iter() {
                self.monkeys
                    .get_mut(index)
                    .expect("monkey at index must exist to catch items")
                    .catch(item);
            }
        }
    }
}
```

And then for `part1`:

```rust
let worry_fix = |v| v / 3;

for _i in 0..20 {
    monkey_pile.step(&worry_fix);
}
```

There is one interesting bit:

```rust
type MonOp = dyn Fn(isize) -> isize;
type BinOp = fn(isize, isize) -> isize;
```

Why are those different? 

In a nutshell, `fn` is the type of functions (*not* closure) and `Fn` is a trait (thus `dyn`, it can be any type that matches that trait) that matches functions *and* closures. We can't directly use `type MonOp = fn(isize) -> isize`, since the actual `worry_fix` is a closure:

```rust
// All tests are divisibility tests, so we only need to word mod(lcm(...))
// I don't see an LCM function in the stdlib, so this will work (just less efficient)
let mut worry_value = 1;
for monkey in monkey_pile.monkeys.iter() {
    worry_value *= monkey.test_divisor;
}
let worry_fix = move |v| v % worry_value;
```

We capture `worry_value`. I can't really see any way about that. Macros perhaps? But we still wouldn't have the value at compile time, so that wouldn't work. 

In any case, changing to `Fn` and allowing closures works great. 

An interesting finding. 

#### Performance

```bash
$ ./target/release/11-monkeyator 1 data/11.txt

99840
took 133.541µs

$ ./target/release/11-monkeyator 2 data/11.txt

20683044837
took 11.15325ms
```

Well, running 10,000 cycles certainly does take a bit longer. Got a solution quickly enough though and learned a few new things, so all is well. And we're still in a fraction of a second though, so... onward!
