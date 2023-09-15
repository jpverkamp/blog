---
title: "AoC 2022 Day 13: List Parsinator"
date: 2022-12-13 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Parsing
---
## Source: [Distress Signal](https://adventofcode.com/2022/day/13)

## Part 1

> Given pairs of `Signal`s (where a `Signal` is a nested list ;example: `[[1],[2,3,4]]`), count how many pairs are 'in order'. 

One `Signal` is less than the other if: 

* Both are an integer and the first is less than the second
* Both are a list and the first value is less than the second
  * If the first values are the same, compare the second
  * If the first has fewer elements, it is treated as less than the second
* When comparing an integer and a list, wrap the integer as a single element list and compare them

<!--more-->

This is actually a pretty fun problem. Basically, it breaks down into two halves: 

* Parse a recursive list structure `From<String>`
* Implement `PartialOrd` for two lists

So let's do it!

First, parsing:

```rust
#[derive(Clone, Debug, Ord, Eq, PartialEq)]
enum Signal {
    Value(u8),
    List(Vec<Signal>),
}

impl From<String> for Signal {
    fn from(line: String) -> Self {
        let stack = RefCell::new(Vec::new());
        let current_number = RefCell::new(String::new());

        // Push an initial 'wrapper' list that we'll remove before returning
        stack.borrow_mut().push(Signal::List(Vec::new()));

        // Helper function that will check if we're currently parsing a number
        // If so, push it onto the current list (malformed input if it's not a list)
        let try_push_number = || {
            if current_number.borrow().is_empty() {
                return;
            }
            let value = current_number
                .borrow()
                .parse::<u8>()
                .expect("number should be a number");

            current_number.borrow_mut().clear();

            match stack
                .borrow_mut()
                .last_mut()
                .expect("must still have one item to push to")
            {
                Signal::List(v) => {
                    v.push(Signal::Value(value));
                }
                _ => panic!("malformed stack, expected list to put thing in"),
            }
        };

        // Process the input one char at a time
        for c in line.chars() {
            match c {
                // Start a new nested list
                '[' => {
                    stack.borrow_mut().push(Signal::List(Vec::new()));
                }
                // Finish the most recent nested list
                // Make sure to finish a number if we were parsing one
                // Then push this list into the one before it as an element
                ']' => {
                    try_push_number();

                    let thing = stack.borrow_mut().pop().expect("mismatched []");
                    match stack
                        .borrow_mut()
                        .last_mut()
                        .expect("must still have one item to push to")
                    {
                        Signal::List(v) => {
                            v.push(thing);
                        }
                        _ => panic!("malformed stack, expected list to put thing in"),
                    }
                }
                // Finish the current number and start a new one
                ',' => {
                    try_push_number();
                }
                // Building up a number one digit at a time
                c if c.is_digit(10) => {
                    current_number.borrow_mut().push(c);
                }
                // Anything else is bad input
                _ => panic!("unexpected char {}", c),
            }
        }

        // Verify that we have exactly one element left
        assert_eq!(stack.borrow().len(), 1);
        let wrapper = stack.borrow_mut().pop().unwrap();

        // Unwrap the initial 'wrapper' list we made at the beginning
        match wrapper {
            Signal::List(v) if v.len() == 1 => v[0].clone(),
            _ => panic!("must end with the final wrapper list with only one element"),
        }
    }
}
```

I've commented the heck out of it, but what it boils down to is that you have three special characters:

* `[` starts a sublist
* `,` delimits elements, finishing the parsing of a number 
* `]` ends a sublist (and also finishing the parsing of a number)

Anything else is part of a digit. So we build up the numbers and keep a stack of which list we're currently building up on. When we finish a list, attach it to the parent.

There's one interesting bit in that we wrap the whole thing up in an initial `List`. This mostly makes the parsing easier. We don't need a special case for the first level, just remove the wrapper at the end. 

Now that we have the lists, we want to `PartialOrd` them:

```rust
// Doing PartialOrd instead of Ord to get the 'correct' default behavior for Vecs in List
impl PartialOrd for Signal {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        use Signal::*;

        match (self, other) {
            // Two values or two lists use the built in partial_cmp functions
            (Value(a), Value(b)) => a.partial_cmp(b),
            (List(a), List(b)) => a.partial_cmp(b),
            // One of each turns the value into a singleton list and then compares
            (Value(a), List(..)) => List(vec![Value(*a)]).partial_cmp(other),
            (List(..), Value(b)) => self.partial_cmp(&List(vec![Value(*b)])),
        }
    }
}
```

We do have two choices here: implementing `Ord` or `PartialOrd`. In this case, since we're relying on the `Ord`/`PartialOrd` implementation of `u8` and `Vec`, we want `PartialOrd`. Specifically, `Ord` will return the opposite value we want for lists of unequal length. 

And there we have it:

```rust
fn part1(filename: &Path) -> String {
    let mut lines = iter_lines(filename).peekable();
    let mut sum_of_ordered = 0;

    // Iterate over pairs of input
    for index in 1.. {
        // If is_none, we've reached the end of the file
        if lines.peek().is_none() {
            break;
        }

        // Read the signals, consume the next newline if there is one (otherwise EOF)
        let s1 = Signal::from(lines.next().expect("must have first signal"));
        let s2 = Signal::from(lines.next().expect("must have second signal"));
        lines.next_if_eq(&"");

        if s1 < s2 {
            sum_of_ordered += index;
        }
    }

    sum_of_ordered.to_string()
}
```

Grab the pairs of `Signal`, compare with `s1 < s2` (how cool is that) and sum of the indexes in the right order. 

## Part 2

> Take all `Signal`s and add two special 'divider' values: `[[2]]` and `[[6]]`. Sort the entire list and return the product of the indices where the 'dividers' end up.

Nothing new to do here, just literally turn it into code:

```rust
fn part2(filename: &Path) -> String {
    // Remove newlines and parse everything else as signals
    let mut signals = iter_lines(filename)
        .filter(|line| !line.is_empty())
        .map(Signal::from)
        .collect::<Vec<_>>();

    // Define and add our 'divider' signals
    let dividers = vec![
        Signal::from(String::from("[[2]]")),
        Signal::from(String::from("[[6]]")),
    ];

    for divider in dividers.iter() {
        signals.push(divider.clone());
    }

    signals.sort();

    // Extract the indices of any dividers and multiply as requested
    dividers
        .iter()
        .map(|d| 1 + signals.iter().position(|s| s == d).unwrap())
        .product::<usize>()
        .to_string()
}
```

`signals.iter().position` was a fun little bit to find the dividers. I do like writing mostly-[[wiki:functional programming]]() style Rust. 

## Performance

We're really not doing much, the heavy part is the parsing honestly. So it's fast:

```rust
$ ./target/release/13-list-parsinator 1 data/13.txt

5506
took 1.420833ms

./target/release/13-list-parsinator 2 data/13.txt

21756
took 2.013041ms
```