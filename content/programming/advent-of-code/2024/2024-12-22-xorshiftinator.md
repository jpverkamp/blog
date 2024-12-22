---
title: "AoC 2024 Day 22: Xorshiftinator"
date: 2024-12-22 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Random Number Generators
- Pseudo Random Number Generators
- Xorshift
- Visualization
- Data Structures
- Bit shifts
---
## Source: [Day 22: Monkey Market](https://adventofcode.com/2024/day/22)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day22.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Implement a [[wiki:PRNG]]() with the following update function:
>
> 1. Multiply by 64, xor with the previous value, [[wiki:modulo]]() 16777216
> 2. Divide by 32, xor with the previous value (from step 1), modulo 16777216
> 3. Multiply by 2048, xor with the previous value (from step 2), module 16777216
>
> For each of a series of seeds, sum the 2000th generated number. 

<!--more-->

Those are all powers of 2... This is an [[wiki:xorshift]]() random number generator (or a shift-register generator). 

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct SuperSecretPseudoRandomNumberGenerator {
    value: u64,
}

impl SuperSecretPseudoRandomNumberGenerator {
    pub fn new(seed: u64) -> Self {
        Self { value: seed }
    }
}

impl Iterator for SuperSecretPseudoRandomNumberGenerator {
    type Item = u64;

    fn next(&mut self) -> Option<u64> {
        self.value ^= self.value << 6; // times 64, mix
        self.value &= 0x00FF_FFFF;
        self.value ^= self.value >> 5; // divide by 32, mix
        self.value &= 0x00FF_FFFF;
        self.value ^= self.value << 11; // times 2048, mix
        self.value &= 0x00FF_FFFF;

        Some(self.value)
    }
}
```

Which makes part 1:

```rust
#[aoc_generator(day22)]
pub fn parse(input: &str) -> Vec<u64> {
    input.lines().map(|line| line.parse().unwrap()).collect()
}

#[aoc(day22, part1, v1)]
fn part1_v1(input: &[u64]) -> u64 {
    input
        .iter()
        .map(|&seed| {
            SuperSecretPseudoRandomNumberGenerator::new(seed)
                .into_iter()
                .nth(1999) // It's zero based :)
                .unwrap()
        })
        .sum()
}
```

Woot. 

```bash
$ cargo aoc --day 22 --part 1

AOC 2024
Day 22 - Part 1 - v1 : 13764677935
	generator: 80.5µs,
	runner: 8.88625ms
```

I expect I'm losing a bit from the levels of abstraction, but really, I'm not *doing* anything extra here, so I don't expect I'm going to get the runtime down much from that. 

## Part 2

> For each super secret pseudo random number generator™, calculate a running difference of the ones digit of each generated number. So if the sequence (of ones digits) was `[1, 7, 3, 5, 6, ...]` the running differences would be `[6, -4, 2, 1, ...]`. 
>
> For a given 4-number running difference sequence and for each seed, score the based on the index of when that sequence is first detected (with no score after index=2000). 
>
> Find the 4-number sequence that has the largest sum of scores across all of the input seeds. 

Well that's certainly a mess. :smile:

### Brute force

Okay, first try, brute force it! Let's write a function to score all inputs based on a given sequence and then try *all of them*!

```rust
#[aoc(day22, part2, bruteforce)]
fn part2_bruteforce(input: &[u64]) -> usize {
    fn banana_score(input: &[u64], seq: &[i8]) -> usize {
        input
            .iter()
            .map(|&seed| {
                let mut rng = SuperSecretPseudoRandomNumberGenerator::new(seed);
                let mut previous_ones = (seed % 10) as i8;
                let mut delta_buffer = VecDeque::new();

                let mut index = 0;
                loop {
                    index += 1;
                    let value = rng.next().unwrap();
                    let ones = (value % 10) as i8;

                    delta_buffer.push_back(ones - previous_ones);
                    if delta_buffer.len() > 4 {
                        delta_buffer.pop_front();
                    }

                    previous_ones = ones;

                    if delta_buffer.len() == 4
                        && delta_buffer[0] == seq[0]
                        && delta_buffer[1] == seq[1]
                        && delta_buffer[2] == seq[2]
                        && delta_buffer[3] == seq[3]
                    {
                        break;
                    }

                    if index >= 2_000 {
                        return 0;
                    }
                }

                previous_ones as usize
            })
            .sum()
    }

    repeat_n(-9..=9, 4)
        .multi_cartesian_product()
        .map(|seq| banana_score(input, seq.as_slice()))
        .max()
        .unwrap()
}
```

The banana score function is a bit heavier than I'd like it to be, but there's only a bit of room for improvement there. Basically, we iterate through values and pull off the `ones` digit, then we feed it into a `VecDeque` which is working as a [[wiki:ring buffer]]() for me. Then {{<crate itertools>}} gives us `repeat_n` + `multi_cartesian_product`, which is effectively 'permutations with replacement' (as suggested in [the docs](https://docs.rs/itertools/latest/itertools/trait.Itertools.html#method.permutations)). 

```bash
$ cargo aoc --day 22 --part 2

AOC 2024
Day 22 - Part 2 - bruteforce : 1619
	generator: 50.75µs,
	runner: 1741.269152208s
```

lol. 

I actually let that run overnight, since I saw it was making good progress and this isn't an exponential problem, just a big one. That's just under half an hour. :smile:

The one optimization I did try on this was to skip over any impossible values. For example, you can never see a delta of `[-9, -1]` since that would mean that we started at any value, then dropped by 9, then by another 1... which wouldn't fit in a single digit. 

Running this:

```bash
$ cargo aoc --day 22 --part 2

Day 22 - Part 2 - bruteforce : 1619
	generator: 36.084µs,
	runner: 810.663676041s
```

That's only 13 minutes, so roughly twice as fast! The video in [the visualization section](#visualizations) shows this: there is a roughly 1/4 section on the top left and bottom right that is exactly this pattern of impossible values. 

But... that's still **minutes** long. We can do better!

### Scan for sequence scores

Instead of trying every sequence, let's run each seed through the first 2000 steps, keeping a running ring buffer. At each step, if it's a ring buffer we've never seen before (for this seed), record the index in a `HashMap`. This will give us the score for this seed for every viable sequence and it's `O(2000)` (constant time with a huge constant :smile:)

Then, in between each sequence, combine these into a global `HashMap`, adding entries we haven't already seen and summing those we have. 

```rust
#[aoc(day22, part2, seqscore)]
fn part2_seqscore(input: &[u64]) -> usize {
    let mut sequence_scores = HashMap::new();

    input.iter().for_each(|&seed| {
        // Find the first time each sequence appears and store the score for that sequence
        let mut local_sequence_scores = HashMap::new();
        let mut delta_buffer = VecDeque::new();

        SuperSecretPseudoRandomNumberGenerator::new(seed)
            .into_iter()
            .take(2_000)
            .fold((seed % 10) as i8, |previous_ones, value| {
                let ones = (value % 10) as i8;

                delta_buffer.push_back(ones - previous_ones);
                if delta_buffer.len() > 4 {
                    delta_buffer.pop_front();
                }

                if delta_buffer.len() == 4 {
                    let key = (
                        delta_buffer[0],
                        delta_buffer[1],
                        delta_buffer[2],
                        delta_buffer[3],
                    );
                    if !local_sequence_scores.contains_key(&key) {
                        local_sequence_scores.insert(key, ones as usize);
                    }
                }

                ones
            });

        // Add the new local sequence scores to the overall map
        local_sequence_scores.into_iter().for_each(|(key, value)| {
            sequence_scores
                .entry(key)
                .and_modify(|v| *v += value)
                .or_insert(value);
        });
    });

    // Find whichever sequence has the highest overall score
    sequence_scores
        .into_iter()
        .map(|(_key, value)| value)
        .max()
        .unwrap()
}
```

I did rewrite this in a bit more functional style, they're basically equivalent. The possibly weird bit here is the `fold`. Basically, a fold runs through a list and keeps some sort of accumulated value. In this case, that's whatever the previous iteration had as `ones`. 

All that and we have an answer:

```bash
$ cargo aoc --day 22 --part 2

AOC 2024
Day 22 - Part 2 - seqscore : 1619
	generator: 35.458µs,
	runner: 96.270583ms
```

### Packing a single `u32` instead of a `VecDeque`

Since we're already doing a bunch with bit shifting already, I got the idea to use a `u32` representing four 5-bit numbers (to hold -9..9) as the buffer:

```rust
// ...

delta_buffer <<= 5;
delta_buffer |= (ones - previous_ones + 9) as u32;
delta_buffer &= 0b11111_11111_11111_11111;

if index > 4 && !local_sequence_scores.contains_key(&delta_buffer) {
    local_sequence_scores.insert(delta_buffer, ones as usize);
}
// ...
```

It's not actually any faster:


```bash
$ cargo aoc --day 22 --part 2

AOC 2024
Day 22 - Part 2 - seqscore : 1619
	generator: 35.458µs,
	runner: 96.270583ms

Day 22 - Part 2 - bitbuffer : 1619
	generator: 130.541µs,
	runner: 105.354917ms
```

But it's a fun change!

### Visualizations

Okay, here are a few different visualizations that I worked out today.


First, we have the evolving distribution of each difference sequence's score over time as a heatmap:

<video controls src="/embeds/2024/aoc/day22-part2.mp4"></video>

For a sequence `(a, b, c, d)`, `a` and `b` make the `x` coordinate with `a` being across the entire axis and `b` repeated every 20 values. That's why we have no entries in either corner, that would be two negative numbers summing over -10 or two positive over 10. 

Here we have a few stills generated from the seed=123.

This is all of the bits generated from the first $400 * 20 = 8000$ values. Values are 20 bits long, so each row is 20 values of 20 bits each:

{{<figure src="/embeds/2024/aoc/day22-part1-bits.png">}}

This is $400 * 400 = 160000$ values, each rendered as an RGB color. Because we have 20 bits, I used the lowest six for red, the next six for green, and the last six for blue and dropped the highest two.

{{<figure src="/embeds/2024/aoc/day22-part1-rgb.png">}}

And here is a map of the `ones` that we used in [part 2](#part-2). It's a value 0-9, so black is 0 and bright green is 9. 

{{<figure src="/embeds/2024/aoc/day22-part1-ones.png">}}

If this was a particularly bad random number generator, you would start to see repeating patterns in these values. Because we don't... well, that doesn't mean the RNG is good, but it at least isn't obviously terrible? 

### Ones stats

I also went ahead and calculate some stats on the ones.

If you run 1,000,000 rounds and count how many you see of each ones digit:

| digit | count  | percent |
| ----- | ------ | ------- |
| 0     | 99981  | 10.00%  |
| 1     | 99694  | 9.97%   |
| 2     | 99985  | 10.00%  |
| 3     | 100421 | 10.04%  |
| 4     | 100133 | 10.01%  |
| 5     | 99877  | 9.99%   |
| 6     | 99800  | 9.98%   |
| 7     | 99885  | 9.99%   |
| 8     | 100042 | 10.00%  |
| 9     | 100182 | 10.02%  |

If you count how many times you see each pair of digits (which would control the deltas):

|     | 0     | 1     | 2     | 3     | 4     | 5     | 6     | 7     | 8     | 9     |
| --- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| 0   | 10107 | 9954  | 9996  | 10045 | 9875  | 9879  | 10039 | 9982  | 10015 | 10090 |
| 1   | 9934  | 10010 | 10123 | 10007 | 10048 | 9942  | 9800  | 9961  | 9920  | 9949  |
| 2   | 9951  | 9996  | 10030 | 9962  | 10081 | 9913  | 10090 | 9931  | 9982  | 10049 |
| 3   | 10070 | 10012 | 10050 | 10064 | 10044 | 10140 | 10061 | 10025 | 10000 | 9955  |
| 4   | 9908  | 10022 | 9897  | 10133 | 10195 | 10012 | 10027 | 9896  | 10013 | 10029 |
| 5   | 10008 | 9851  | 10064 | 9998  | 9964  | 9958  | 10097 | 10154 | 9804  | 9979  |
| 6   | 10018 | 9991  | 9828  | 10134 | 9987  | 10009 | 9943  | 9854  | 10026 | 10010 |
| 7   | 10030 | 10025 | 9899  | 9914  | 9798  | 9892  | 9949  | 10110 | 10129 | 10139 |
| 8   | 10080 | 9933  | 9907  | 10138 | 10104 | 10038 | 9815  | 9893  | 10088 | 10046 |
| 9   | 9875  | 9900  | 10191 | 10026 | 10037 | 10094 | 9979  | 10079 | 10065 | 9936  |

And the same as a ratio:

|     | 0    | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    |
| --- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 0   | 1.01 | 1.00 | 1.00 | 1.00 | 0.99 | 0.99 | 1.00 | 1.00 | 1.00 | 1.01 |
| 1   | 0.99 | 1.00 | 1.01 | 1.00 | 1.00 | 0.99 | 0.98 | 1.00 | 0.99 | 0.99 |
| 2   | 1.00 | 1.00 | 1.00 | 1.00 | 1.01 | 0.99 | 1.01 | 0.99 | 1.00 | 1.00 |
| 3   | 1.01 | 1.00 | 1.00 | 1.01 | 1.00 | 1.01 | 1.01 | 1.00 | 1.00 | 1.00 |
| 4   | 0.99 | 1.00 | 0.99 | 1.01 | 1.02 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 |
| 5   | 1.00 | 0.99 | 1.01 | 1.00 | 1.00 | 1.00 | 1.01 | 1.02 | 0.98 | 1.00 |
| 6   | 1.00 | 1.00 | 0.98 | 1.01 | 1.00 | 1.00 | 0.99 | 0.99 | 1.00 | 1.00 |
| 7   | 1.00 | 1.00 | 0.99 | 0.99 | 0.98 | 0.99 | 0.99 | 1.01 | 1.01 | 1.01 |
| 8   | 1.01 | 0.99 | 0.99 | 1.01 | 1.01 | 1.00 | 0.98 | 0.99 | 1.01 | 1.00 |
| 9   | 0.99 | 0.99 | 1.02 | 1.00 | 1.00 | 1.01 | 1.00 | 1.01 | 1.01 | 0.99 |

Seeing all those numbers no further than ±0.02 is a pretty good indication that is a decent enough random number generator. :smile: 

## Benchmarks

```bash
$ cargo aoc bench --day 22

Day22 - Part1/v1        time:   [5.6602 ms 5.7042 ms 5.7508 ms]

Day22 - Part2/seqscore  time:   [97.792 ms 98.759 ms 99.974 ms]
Day22 - Part2/bitbuffer time:   [81.465 ms 81.937 ms 82.441 ms]
```