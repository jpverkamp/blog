---
title: "AoC 2024 Day 13: Cramerinator"
date: 2024-12-13 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Cramer's Rule
- Mathematics
- Brute Force
- Algorithms
- Linear Algebra
---
## Source: [Day 13: Claw Contraption](https://adventofcode.com/2024/day/13)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day13.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given Button A `(ax, ay)`, Button B `(bx, by)`, and Prize `(px, py)`; how many times must you press Button A (`a`) and Button B (`b`) to reach the Prize? Sum `3a + b` for each machine that has a solution. 

<!--more-->

First, some parsing:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ClawMachine {
    a: Point,
    b: Point,
    p: Point,
}

#[aoc_generator(day13)]
fn parse(input: &str) -> Vec<ClawMachine> {
    let mut lines = input.lines();
    let mut machines = vec![];

    fn parse_equation(s: &str) -> Point {
        let (_, input) = s.split_once("X").unwrap();
        let (xs, ys) = input.split_once("Y").unwrap();

        let x = xs[1..(xs.len() - 2)]
            .parse::<i32>()
            .expect("failed to parse x part");
        let y = ys[1..].parse::<i32>().expect("failed to parse y part");

        (x, y).into()
    }

    loop {
        let line = lines.next();
        if line.is_none() {
            break;
        }

        let a = parse_equation(line.unwrap());
        let b = parse_equation(lines.next().unwrap());
        let p = parse_equation(lines.next().unwrap());

        machines.push(ClawMachine { a, b, p });

        // Empty line or end of file
        if lines.next().is_none() {
            break;
        }
    }

    machines
}
```

I fully expect brute forcing not to work for part 2, but for part 1 it should be fine. (We're guaranteed that `0 ≤ a,b ≤ 100`). 

```rust
#[aoc(day13, part1, bruteforce)]
fn part1_bruteforce(input: &[ClawMachine]) -> i32 {
    let mut tokens = 0;

    for machine in input {
        for a_presses in 0..=100 {
            let after_a = machine.p - machine.a * a_presses;

            if after_a.x % machine.b.x == 0
                && after_a.y % machine.b.y == 0
                && after_a.x / machine.b.x == after_a.y / machine.b.y
            {
                let b_presses = after_a.x / machine.b.x;

                tokens += a_presses * 3 + b_presses;
                break;
            }
        }
    }

    tokens
}
```

Loop on `a` first, since it costs more, we want to find the value that minimizes `a` [^lies].

[^lies]: Although it turns out / when you think about it, it's an intersection of two lines. There is always: exactly 1 solution, no solution (if they're parallel), or infinite solutions (if they're on the same line). 

```bash
$ cargo aoc --day 13 --part 1

AOC 2024
Day 13 - Part 1 - bruteforce : 26810
	generator: 127.25µs,
	runner: 105.666µs
```

### Optimization 1: Cramer's Rule

Okay. Now we've looked at the [part 2](#part-2) and know that there is *no* way we're going to be able to brute force it. 

So let's do some math. 

Short version: [[wiki:Cramer's rule]]().

Longer version: 

We are dealing with the equation $ a \overline{A} + b \overline{B} = \overline{P} $. 

Alternatively:

$$ 
a A_x + b B_x = P_x \\\
a A_y + b B_y = P_y
$$

Two equations with two unknowns, so there should be either exactly 1 solution, no solutions (if the lines are parallel), or infinite solutions (if they are co-linear). 

Let's solve:

$$
a A_x + b B_x = P_x \\\
a = \frac{P_x - b B_x}{A_x}
$$

Substitute into the second equation:

$$ 
\frac{P_x - b B_x}{A_x} A_y + b B_y = P_y \\\
$$

Solve for $b$:

$$
\frac{P_x A_y}{A_x} - \frac{b B_x A_y}{A_x} + b B_y = P_y \\\
b B_y - b \frac{B_x A_y}{A_x} = P_y - \frac{P_x A_y}{A_x} \\\
b = \frac{P_y - \frac{P_x A_y}{A_x}}{B_y - \frac{B_x A_y}{A_x}}
$$

Which is a constant value. And we know $a$ above. 

So all we'd have to do is plug in all those values, check if they're integers, and--if so--add $3a + b$. 

This ends up equivalent to making the matrixes:

$$
\overline M =
\begin{vmatrix}
    A_x & B_x \\\
    A_y & B_y
\end{vmatrix} \\\
\overline M_A =
\begin{vmatrix}
    P_x & B_x \\\
    P_y & B_y
\end{vmatrix} \\\
\overline M_B =
\begin{vmatrix}
    A_x & P_x \\\
    A_y & P_y
\end{vmatrix} \\\
$$

And that directly gives us $a$ and $b$:

$$
a = \frac{det(M_A)}{det(M)}
$$ 

and

$$
b = \frac{det(M_B)}{det(M)}
$$

Once again, if $a$ or $b$ is non-integer, we don't have a valid solution for this problem. For the given input, we don't have to worry about 0/infinite solutions, but those would appear here as $det(M) = 0$. 

That's a lot of math, let's turn it into code:

```rust
fn cramer_integer_solve(
    ax: i128,
    ay: i128,
    bx: i128,
    by: i128,
    px: i128,
    py: i128,
) -> Option<(i128, i128)> {
    let det = ax * by - ay * bx;
    let det_sub_a = px * by - py * bx;
    let det_sub_b = ax * py - ay * px;

    if det == 0 || det_sub_a % det != 0 || det_sub_b % det != 0 {
        None
    } else {
        Some((det_sub_a / det, det_sub_b / det))
    }
}

#[aoc(day13, part1, cramer)]
fn part1_cramer(input: &[ClawMachine]) -> u128 {
    let mut tokens = 0;

    for machine in input {
        if let Some((a_presses, b_presses)) = cramer_integer_solve(
            machine.a.x as i128,
            machine.a.y as i128,
            machine.b.x as i128,
            machine.b.y as i128,
            machine.p.x as i128,
            machine.p.y as i128,
        ) {
            if a_presses >= 0 && b_presses >= 0 {
                tokens += a_presses as u128 * 3 + b_presses as u128;
            }
        }
    }

    tokens
}
```

It looks so simple when you say it that way. :smile:

(We don't actually end up needing the `>= 0` checks or the `det == 0` check for this problem, but I left them in anyways.)

And quick too:

```bash
$ cargo aoc --day 13 --part 1

AOC 2024
Day 13 - Part 1 - bruteforce : 26810
	generator: 127.25µs,
	runner: 105.666µs

Day 13 - Part 1 - cramer : 77064
	generator: 102.125µs,
	runner: 4.666µs
```

## Part 2

> Add 10 billion to the `(x, y)` of the Prize.

Yup. Big numbers. 

Other than modifying the `ClawMachine` though, it just works:

```rust
#[aoc(day13, part2, cramer)]
fn part2_cramer(input: &[ClawMachine]) -> u128 {
    let mut tokens = 0;

    for machine in input {
        if let Some((a_presses, b_presses)) = cramer_integer_solve(
            machine.a.x as i128,
            machine.a.y as i128,
            machine.b.x as i128,
            machine.b.y as i128,
            machine.p.x as i128 + 10_000_000_000_000,
            machine.p.y as i128 + 10_000_000_000_000,
        ) {
            if a_presses >= 0 && b_presses >= 0 {
                tokens += a_presses as u128 * 3 + b_presses as u128;
            }
        }
    }

    tokens
}
```

Still fast:

```bash
$ cargo aoc --day 13 --part 2

AOC 2024
Day 13 - Part 2 - cramer : 108713182988244
	generator: 123.959µs,
	runner: 12.583µs
```

## Benchmarks

```bash
$ cargo aoc bench --day 13

Day13 - Part1/bruteforce   time:   [23.116 µs 23.249 µs 23.415 µs]
Day13 - Part1/cramer       time:   [741.83 ns 746.53 ns 751.96 ns]
Day13 - Part2/cramer       time:   [5.7927 µs 5.8130 µs 5.8341 µs]
```

Nanoseconds woot!

## Optimization 2: Really going off the deep end

Let's see just *how* fast we can make this, including the parsing. 

First, a macro that will inline parse an unsigned integer from a byte array:

```rust
macro_rules! fast_parse_u32 {
    ($input:expr, $index:expr, $skip:expr) => {{
        $index += $skip;

        let mut result = 0;

        while $index < $input.len() {
            let byte = $input[$index];

            if !byte.is_ascii_digit() {
                break;
            }

            result = result * 10 + (byte - b'0') as u32;
            $index += 1;
        }

        result
    }};
}
```

And then code that can use that + inline Cramer's rule:

```rust
pub fn part1(input: &str) -> String {
    let mut tokens = 0;

    let input = input.as_bytes();
    let mut index = 0;
    while index < input.len() {
        let ax = fast_parse_u32!(input, index, 12) as i32;
        let ay = fast_parse_u32!(input, index, 4) as i32;
        let bx = fast_parse_u32!(input, index, 13) as i32;
        let by = fast_parse_u32!(input, index, 4) as i32;
        let px = fast_parse_u32!(input, index, 10) as i32;
        let py = fast_parse_u32!(input, index, 4) as i32;


        let det = ax * by - ay * bx;
        let det_sub_a = px * by - py * bx;
        if det_sub_a % det == 0 {
            let det_sub_b = ax * py - ay * px;
            if det_sub_b % det == 0 {
                tokens += 3 * det_sub_a / det + det_sub_b / det;
            }
        }

        index += 2;
    }

    tokens.to_string()
}
```

The ugliest part, I think, is the hardcoded `$skip` values. That's the `Button A: X+`, `, Y+`, etc parts. The `index += 2` at the end is to skip the double newline between problems; this also handles the `index < input.len()` case at the top when we want to start. 

It does also drop the `det == 0` and `a` or `b` being <= cases as mentioned above. There are no cases of this in my input at least. 

For part 2, the only changes are adding 10 billion to `px` and `py` after parsing them. 

So how does it perform?

```bash
Day13 - Part1/bruteforce    time:   [23.116 µs 23.249 µs 23.415 µs]
Day13 - Part1/cramer        time:   [741.83 ns 746.53 ns 751.96 ns]
Day13 - Part2/cramer        time:   [5.7927 µs 5.8130 µs 5.8341 µs]

day13/day13_part1           time:   [13.225 µs 13.465 µs 13.788 µs]
day13/day13_part2           time:   [13.645 µs 13.699 µs 13.761 µs]
```

These times are actually slower than the benchmarks above... but that's because those don't include parsing. To get an idea about how long the parsing (the `generator` part) takes:

```rust
cargo aoc --day 13

AOC 2024
Day 13 - Part 1 - bruteforce : 26810
	generator: 70.5µs,
	runner: 29.042µs

Day 13 - Part 1 - cramer : 26810
	generator: 57.75µs,
	runner: 3.041µs

Day 13 - Part 2 - cramer : 108713182988244
	generator: 56.708µs,
	runner: 5.167µs
```

I'm not actually sure why the `bruteforce` generator runs slower, it's fairly consistent. But they all 3 use the same one, so it should be roughly the same. My best guess? `bruteforce` runs first, so the input file is cached for the other two. 

In any case, the *entire* optimized solution runs ~4x as fast as the entire parser. 

And honestly, the code isn't even that bad! 

I probably won't do this too often, but I think this was a good one to try it on. 