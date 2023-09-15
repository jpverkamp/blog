---
title: "AoC 2022 Day 20: Deencryptinator"
date: 2022-12-20 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Encryption
- Ciphers
- Modular Arithmetic
---
## Source: [Grove Positioning System](https://adventofcode.com/2022/day/20)

## Part 1

> Given a list of numbers `mix` them by moving each number forward/backward in the list based on it's value. For example, in `4, -2, 5, 6, 7, 8, 9` moving the `-2` will result in `4, 5, 6, 7, 8, -2, 9`. Each number should be moved exactly once in the *original order* they appeared in the list. 

<!--more-->

That's a very strange description. Originally, I was planning to essentially create two level linked list (I have no idea if there's an 'official' name for this). Each node would hold a number, the first linked list would iterate through the numbers in the original order (and never change) and the second level would iterate through the numbers in their current order (and change with each `mix`). 

I still think that this would be the most 'elegant' way to go about this from an algorithmic case, ... but I just couldn't get the data structure to work out right in Rust. I may have to come back to this one yet. 

So instead we have:

```rust
type INumber = i128;

#[derive(Clone, Debug)]
struct Message {
    data: Vec<(usize, INumber)>,
}

impl<I> From<&mut I> for Message
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        Message {
            data: iter
                .map(|line| line.parse::<INumber>().expect("must be a number"))
                .enumerate()
                .collect::<Vec<_>>(),
        }
    }
}
```

I'll come back to why I made `INumber`. Hint: really really big numbers. 

In a nutshell, the data is stored as tuples of `(original index, value)`. That way when the order is scrambled, I can still come through and figure out where the number with the next `original_index` is now. 

After that, we have the mixing function:

```rust
impl Message {
    fn mix(&mut self, index_to_move: usize) {
        let (index_current, (_, value)) = self
            .data
            .iter()
            .enumerate()
            .find(|(_, (index_original, _))| index_to_move == *index_original)
            .unwrap();

        let mut index_target = index_current as INumber + value;
        let ilen = self.data.len() as INumber;

        // If the index is negative, increase it into range
        // We can't jump directly there because we'll overflow even i128, so jump in decreasing steps
        while index_target < 0 {
            index_target += ilen - 1;
        }

        while index_target >= ilen {
            let loops = index_target / ilen;
            index_target = index_target - loops * ilen + loops;
        }

        // If we were jumping downwards and ended up at 0, we actually want it at the end
        // Most to match the given test case, this doesn't matter for the real answers
        if index_target == 0 && *value < 0 {
            index_target = ilen - 1;
        }

        let index_target = index_target as usize;
        let removed = self.data.remove(index_current);
        self.data.insert(index_target, removed);
    }

    fn len(&self) -> usize {
        self.data.len()
    }

    #[allow(dead_code)]
    fn data(&self) -> Vec<INumber> {
        self.data.iter().map(|(_, v)| *v).collect::<Vec<_>>()
    }
}
```

One thing that I really wanted to do was to use [[wiki:modular arithmetic]](), but alas. The behavior on negative numbers (returning a negative number) is not what I actually want. I could have just added one more size (which is something I just thought of now), but this works as well enough. 

As I did mention, the finding the `index_current` (which is the currently shuffled index) that matches the `index_to_move` is the first trick. After that, we don't care about the index. 

The other gotcha is that while the number is moving, the list is one element shorter. That one bit me a bit. 

With that, we decrypt my moving each number in turn:

```rust
impl Message {
    fn decrypt(&mut self) {
        for index_to_move in 0..self.len() {
            self.mix(index_to_move);
        }
    }
}
```

And then finally to get the input we actually want, we need the 1000th, 2000th, and 3000th elements *after the current position of the element with value 0*. (Took me a bit to notice that bit of the instructions):

```rust
fn part1(filename: &Path) -> String {
    let mut message = Message::from(&mut iter_lines(filename));
    message.decrypt();

    let index_zero = message
        .data
        .iter()
        .enumerate()
        .find(|(_, (_, v))| *v == 0)
        .unwrap()
        .0;

    (message.data[(index_zero + 1000) % message.len()].1
        + message.data[(index_zero + 2000) % message.len()].1
        + message.data[(index_zero + 3000) % message.len()].1)
        .to_string()
}
```

Sweet. 

## Part 2

> Multiply every value by 811589153 and then mix the list 10 times (still using the original order). 

Theoretically, the original code would have worked great for this, but not using modular arithmetic is biting me now. It's much slower to loop. And then once I solved that, I ran into another big issue: `integer overflow`. The `i128` solved the latter, but for the former I ended up doing something... a bit strange:

```rust
impl Message {
    fn mix(&mut self, index_to_move: usize) {
        let (index_current, (_, value)) = self
            .data
            .iter()
            .enumerate()
            .find(|(_, (index_original, _))| index_to_move == *index_original)
            .unwrap();

        let mut index_target = index_current as INumber + value;
        let ilen = self.data.len() as INumber;

        // If the index is negative, increase it into range
        // We can't jump directly there because we'll overflow even i128, so jump in decreasing steps
        let mut steps = 100000000;
        while steps > 1 {
            while index_target < -steps * ilen {
                let loops = (-index_target / ilen).min(steps);
                index_target += loops * ilen - loops;
            }
            steps /= 10;
        }
        while index_target < 0 {
            index_target += ilen - 1;
        }

        // Do the same if the index is too big, resetting steps
        steps = 10000000;
        while steps > 1 {
            while index_target >= steps * ilen {
                let loops = (index_target / ilen).min(steps);
                index_target = index_target - loops * ilen + loops;
            }
            steps /= 10;
        }
        while index_target >= ilen {
            let loops = index_target / ilen;
            index_target = index_target - loops * ilen + loops;
        }

        // If we were jumping downwards and ended up at 0, we actually want it at the end
        // Most to match the given test case, this doesn't matter for the real answers
        if index_target == 0 && *value < 0 {
            index_target = ilen - 1;
        }

        let index_target = index_target as usize;

        if cfg!(debug_assertions) {
            println!(
                "{} [moving, orig: {:2}, value: {:2}, curr: {:2}, next: {:2}]",
                self, index_to_move, value, index_current, index_target,
            );
        }

        let removed = self.data.remove(index_current);
        self.data.insert(index_target, removed);
    }

    fn len(&self) -> usize {
        self.data.len()
    }

    #[allow(dead_code)]
    fn data(&self) -> Vec<INumber> {
        self.data.iter().map(|(_, v)| *v).collect::<Vec<_>>()
    }
}
```

Essentially, I start by jumping `10,000,000` times the length of the list towards the proper value. Then `1,000,000` and stepping down as I pass each value. This is weird... but it works? And it works pretty fast. 

The new wrapper becomes:

```rust
fn part2(filename: &Path) -> String {
    let mut message = Message::from(&mut iter_lines(filename));
    message.data.iter_mut().for_each(|p| p.1 *= 811589153);
    for _round in 0..10 {
        message.decrypt();
    }

    let index_zero = message
        .data
        .iter()
        .enumerate()
        .find(|(_, (_, v))| *v == 0)
        .unwrap()
        .0;

    (message.data[(index_zero + 1000) % message.len()].1
        + message.data[(index_zero + 2000) % message.len()].1
        + message.data[(index_zero + 3000) % message.len()].1)
        .to_string()
}
```

I like that we can just `iter_mut` over the data and then loop the `decrypt` function. Pretty shiny. 

## Unit testing

Something I really should have been doing throughout these problems that came to a head during this problem: [[wiki:unit testing]](). I have always been testing my two answers (to make sure it stays stable), but for this one, the `mix` function just has so many edge cases... So to make sure that each fix kept working for later cases:

```rust
#[cfg(test)]
mod tests {
    use crate::{part1, part2, Message};
    use aoc::aoc_test;

    fn make_test() -> Message {
        Message {
            data: vec![(0, 1), (1, 2), (2, -3), (3, 3), (4, -2), (5, 0), (6, 4)],
        }
    }

    fn make_zeroes(size: usize) -> Message {
        Message {
            data: (0..size).map(|v| (v, 0)).collect::<Vec<_>>(),
        }
    }

    fn make_singleton(size: usize, index: usize, value: crate::INumber) -> Message {
        let mut message = make_zeroes(size);
        message.data[index].1 = value;
        message
    }

    #[test]
    fn test_mix() {
        let mut message = make_test();
        assert_eq!(message.data(), vec![1, 2, -3, 3, -2, 0, 4]);

        message.mix(0);
        assert_eq!(message.data(), vec![2, 1, -3, 3, -2, 0, 4]);

        message.mix(1);
        assert_eq!(message.data(), vec![1, -3, 2, 3, -2, 0, 4]);

        message.mix(2);
        assert_eq!(message.data(), vec![1, 2, 3, -2, -3, 0, 4]);

        message.mix(3);
        assert_eq!(message.data(), vec![1, 2, -2, -3, 0, 3, 4]);

        message.mix(4);
        assert_eq!(message.data(), vec![1, 2, -3, 0, 3, 4, -2]);

        message.mix(5);
        assert_eq!(message.data(), vec![1, 2, -3, 0, 3, 4, -2]);

        message.mix(6);
        assert_eq!(message.data(), vec![1, 2, -3, 4, 0, 3, -2]);
    }

    #[test]
    fn test_decrypt() {
        let mut message = make_test();
        message.decrypt();
        assert_eq!(message.data(), vec![1, 2, -3, 4, 0, 3, -2]);
    }

    #[test]
    fn test_zeros() {
        let mut message = make_zeroes(9);
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, 0, 0]);

        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn test_singleton() {
        let mut message = make_singleton(9, 4, 1);
        assert_eq!(message.data(), vec![0, 0, 0, 0, 1, 0, 0, 0, 0]);

        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 1, 0, 0, 0]);
    }

    #[test]
    fn test_small_forward() {
        let mut message = make_singleton(9, 4, 2);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 2, 0, 0]);
    }

    #[test]
    fn test_looped_forward() {
        let mut message = make_singleton(9, 4, 5);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 5, 0, 0, 0, 0, 0, 0, 0]);

        let mut message = make_singleton(9, 4, 4);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, 0, 4]);
    }

    #[test]
    fn test_double_looped_forward() {
        let mut message = make_singleton(9, 4, 14);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 14, 0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn test_small_backward() {
        let mut message = make_singleton(9, 4, -2);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, -2, 0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn test_exact_loop_backward() {
        let mut message = make_singleton(9, 2, -2);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, 0, -2]);
    }

    #[test]
    fn test_looped_backward() {
        let mut message = make_singleton(9, 4, -4);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, 0, -4]);

        let mut message = make_singleton(9, 4, -8);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, -8, 0, 0, 0, 0]);

        let mut message = make_singleton(9, 4, -5);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, 0, -5, 0]);

        let mut message = make_singleton(9, 1, -3);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, -3, 0, 0]);
    }

    #[test]
    fn test_double_looped_backward() {
        let mut message = make_singleton(9, 4, -14);
        message.decrypt();
        assert_eq!(message.data(), vec![0, 0, 0, 0, 0, 0, -14, 0, 0]);
    }

    #[test]
    fn test1() {
        aoc_test("20", part1, "19070")
    }

    #[test]
    fn test2() {
        aoc_test("20", part2, "14773357352059")
    }
}
```

I test not mixing, mixing forward and backwards, and each of those looping once or more than once. Each case does slightly different things. I also had a few edge cases (literally) where a number could be either the first or last element in the list, which didn't matter for the actual problem statement (since it's a looped list) but for the purposes of my tests, i wanted to match the examples given. 

It's a decent enough way to write the tests and easy to run!

```bash
$ cargo test --release --bin 20-deencryptinator

   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished release [optimized] target(s) in 0.45s
     Running unittests src/bin/20-deencryptinator.rs (target/release/deps/20_deencryptinator-008079e4e2c7fe78)

running 13 tests
test tests::test_double_looped_backward ... ok
test tests::test_decrypt ... ok
test tests::test_exact_loop_backward ... ok
test tests::test_double_looped_forward ... ok
test tests::test_looped_backward ... ok
test tests::test_looped_forward ... ok
test tests::test_mix ... ok
test tests::test_singleton ... ok
test tests::test_small_backward ... ok
test tests::test_small_forward ... ok
test tests::test_zeros ... ok
test tests::test1 ... ok
test tests::test2 ... ok

test result: ok. 13 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.21s
```

I did run it in `--release` mode, mostly because the final test cases are much faster that way :smile:

## Performance

```bash
$ ./target/release/20-deencryptinator 1 data/20.txt

19070
took 32.35ms

$ ./target/release/20-deencryptinator 2 data/20.txt

14773357352059
took 203.954833ms
```

Acceptable. Especially after yesterday... 