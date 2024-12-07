---
title: "AoC 2024 Day 7: Mathinator"
date: 2024-12-07 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 7: Bridge Repair](https://adventofcode.com/2024/day/7)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day7.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a result and a list of numbers, determine if any combination of addition (`+`) and/or multiplication (`*`) using all the given numbers in order can return the result. Ignore order of operations. 

<!--more-->

Let's do some [[wiki:recursion]]()! Basically, for any given list, take the smaller list consisting of all but the first element. Then check first the case of first element `+` the recur and then `*` the recur. If either of those are true, we're correct. 

```rust
#[aoc(day7, part1, v1)]
fn part1_v1(input: &[Equation]) -> u64 {
    fn is_solvable(target: u64, acc: u64, values: &[u64]) -> bool {
        if values.is_empty() {
            return target == acc;
        }

        is_solvable(target, acc + values[0], &values[1..])
            || is_solvable(target, acc * values[0], &values[1..])
    }

    input
        .iter()
        .filter(|eq| is_solvable(eq.result, 0, &eq.input))
        .map(|eq| eq.result)
        .sum::<u64>()
}
```

One nice thing about this is that we get short circuiting basically for free. It's going to do a [[wiki:depth-first search]]() down all `+`, then all `+` and one `*` etc, and finally all `*`. As soon as any branch returns `true`, all the rest at that level won't be checked. 

```bash
$ cargo aoc --day 7 --part 1

AOC 2024
Day 7 - Part 1 - v1 : 975671981569
	generator: 280.667µs,
	runner: 1.594708ms
```

That's not bad. I bet I could get it under 1ms, but it's good enough for now. 

### Optimization (attempt) 1: Queue

One thing that I'd like to try is to avoid the overhead of function calls. Specifically, instead of keeping the results in the function call stack, instead keep our own:

```rust
#[aoc(day7, part1, queue)]
fn part1_queue(input: &[Equation]) -> u64 {
    input
        .iter()
        .filter(|eq| {
            let mut queue = Vec::with_capacity(2_usize.pow(eq.input.len() as u32));
            queue.push((eq.result, 0, eq.input.as_slice()));

            while let Some((target, acc, values)) = queue.pop() {
                if values.is_empty() {
                    if target == acc {
                        return true;
                    }
                } else {
                    queue.push((target, acc + values[0], &values[1..]));
                    queue.push((target, acc * values[0], &values[1..]));
                }
            }

            false
        })
        .map(|eq| eq.result)
        .sum::<u64>()
}
```

In my opinion, it's actually a bit harder to read this way, but perhaps that's all those years of [[Racket]]()/[[Scheme]]() coming back. :smile:

Amusingly:

```bash
$ cargo aoc --day 7 --part 1

AOC 2024
Day 7 - Part 1 - v1 : 975671981569
	generator: 280.667µs,
	runner: 1.594708ms

Day 7 - Part 1 - queue : 975671981569
	generator: 365.916µs,
	runner: 3.117834ms
```

It doesn't actually perform any better anyways! I should have managed to avoid allocations `with_capacity`, but that doesn't mean there aren't other optimizations this version can't do. So it goes!

## Part 2

> Add the `||` operator: [[wiki:concatenation]]().

That one is going to be a bit more of a pain to implement, but still doable. Basically, to implement `a || b`, we can either convert both to strings, concat, and convert them back... or we can figure out how many digits `b` has (with `log10`) and multiple by `10^that`:

```rust
#[aoc(day7, part2, v1)]
fn part2_v1(input: &[Equation]) -> u64 {
    fn is_solvable(target: u64, acc: u64, values: &[u64]) -> bool {
        if values.is_empty() {
            return target == acc;
        }

        is_solvable(target, acc + values[0], &values[1..])
            || is_solvable(target, acc * values[0], &values[1..])
            || {
                let digits = values[0].ilog10() + 1;
                let multiplier = 10_u64.pow(digits);
                is_solvable(target, acc * multiplier + values[0], &values[1..])
            }
    }

    input
        .iter()
        .filter(|eq| is_solvable(eq.result, 0, &eq.input))
        .map(|eq| eq.result)
        .sum::<u64>()
}
```

How's it do?

```rust
cargo aoc --day 7 --part 2

Day 7 - Part 2 - v1 : 223472064194845
	generator: 170.208µs,
	runner: 42.832875ms
```

We actually have two different problems here: not only is `||` *significantly* slower to compute than `+` or `*`, but we're also checking `O(3^n)` possibilities instead of `O(2^n)`. Still, relatively fast. We'll go with this for now. 

## A 'cleaner' way of looking at it: `OpSet`

One thing that bugged me a bit about this program was how difficult (relatively) it is to extend. To add another operator, you have to add another whole call to `is_solvable` with the new op. What if we could abstract that? 

```rust
struct OpSet {
    ops: Vec<fn(u64, u64) -> u64>,
}

impl OpSet {
    fn new() -> Self {
        Self { ops: vec![] }
    }

    fn include(&mut self, op: fn(u64, u64) -> u64) {
        self.ops.push(op);
    }

    fn can_solve(&self, target: u64, args: &[u64]) -> bool {
        fn recur(me: &OpSet, target: u64, acc: u64, args: &[u64]) -> bool {
            if args.is_empty() {
                return target == acc;
            }

            me.ops
                .iter()
                .any(|op| recur(me, target, op(acc, args[0]), &args[1..]))
        }

        recur(self, target, 0, args)
    }
}
```

Basically, we can create a `struct` that will hold as many binary operators as we want! Then use `any` to check each of them recursively the same as we did before, still short circuiting (`any` does this naturally). 

With that, both solutions become (in my opinion) even cleaner:

```rust
#[aoc(day7, part1, opset)]
fn part1_opset(input: &[Equation]) -> u64 {
    let mut op_set = OpSet::new();
    op_set.include(|a, b| a + b);
    op_set.include(|a, b| a * b);

    input
        .iter()
        .filter(|eq| op_set.can_solve(eq.result, &eq.input))
        .map(|eq| eq.result)
        .sum::<u64>()
}

#[aoc(day7, part2, opset)]
fn part2_opset(input: &[Equation]) -> u64 {
    let mut op_set = OpSet::new();
    op_set.include(|a, b| a + b);
    op_set.include(|a, b| a * b);
    op_set.include(|a, b| {
        let digits = b.ilog10() + 1;
        10_u64.pow(digits) * a + b
    });

    input
        .iter()
        .filter(|eq| op_set.can_solve(eq.result, &eq.input))
        .map(|eq| eq.result)
        .sum::<u64>()
}
```

Nice. 

```bash
$ cargo aoc --day 7

AOC 2024
Day 7 - Part 1 - v1 : 975671981569
	generator: 425.625µs,
	runner: 2.212291ms
    
Day 7 - Part 1 - opset : 975671981569
	generator: 543.959µs,
	runner: 8.823625ms

Day 7 - Part 2 - v1 : 223472064194845
	generator: 141.875µs,
	runner: 42.646083ms
    
Day 7 - Part 2 - opset : 223472064194845
	generator: 313.333µs,
	runner: 131.050583ms
```

A couple times slower though. So it goes. 

## Benchmarks

So how do we do overall? 

```bash
$ cargo aoc bench --day 7

Day7 - Part1/v1         time:   [844.49 µs 851.40 µs 860.95 µs]
Day7 - Part1/queue      time:   [1.3142 ms 1.3193 ms 1.3237 ms]
Day7 - Part1/opset      time:   [3.2182 ms 3.2283 ms 3.2389 ms]

Day7 - Part2/v1         time:   [45.336 ms 45.701 ms 46.153 ms]
Day7 - Part2/opset      time:   [112.29 ms 112.70 ms 113.16 ms]
```

Not bad. Still well under a second, although we're certainly creeping up!

## Future work

In addition to the above, I've also considered a few different potential ways to attack the problem that may (or may not) be faster.

* [[wiki:Memoization]]() - Cache the work we're doing recursively so if we already know a branch doesn't work out, we don't have to do it again. 
* [[wiki:Sorting]]() - For part 1, we can rely on the fact that `+` and `*` have the same [[wiki:precedence]]() in this problem and are [[wiki:commutative]](). Because of that, we should be able to sort the input lists, which should improve memoization (above) or other algorithms.
* [[wiki:Divide and conquer]]() - The problem with `||` is that it's not commutative, but I expect we could split the problem to attack that. 
  * One option would be to calculate all of the different ways that the list can be split up quickly (see above) and then try each ordering of those results (as strings). 
  * Another option would be to split the list and recursively check each half as either 1) only `+` and `*` (which can use the speedups above) and/or 2) including another `||` in that half recursively. 

We'll see if I get to actually doing those though. If you ended up implementing either and it seems faster, I'd love to see it / here about it though!