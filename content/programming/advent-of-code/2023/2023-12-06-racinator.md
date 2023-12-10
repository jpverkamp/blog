---
title: "AoC 2023 Day 6: Racinator"
date: 2023-12-06 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 6: Wait For It](https://adventofcode.com/2023/day/6)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day06) for today (spoilers!)

{{<toc>}}

## Part 1

> Simulate charging up race boats with the behavior that waiting X seconds to start means you move at X units per second. Given time allowed and a target distance, determine how many (integer) numbers of seconds will beat the target distance. 

<!--more-->

### Types and Parsing

Okay, there's minimal input, so this should be quick. The main gotcha is that you get all of the times before all of the distances and then have to `zip` them.

```rust
#[derive(Debug)]
pub struct Race {
    pub time: u64,
    pub record: u64,
}

pub fn races(s: &str) -> IResult<&str, Vec<Race>> {
    let (s, times) = delimited(
        tuple((tag("Time:"), space1)),
        separated_list1(space1, complete::u64),
        newline,
    )(s)?;
    let (s, records) = preceded(
        tuple((tag("Distance:"), space1)),
        separated_list1(space1, complete::u64),
    )(s)?;

    Ok((
        s,
        times
            .into_iter()
            .zip(records)
            .map(|(time, record)| Race { time, record })
            .collect::<Vec<_>>(),
    ))
}
```

### Initial Brute Force Solution

So the obvious answer here would be to just directly try all possible values for X seconds from 0 up to time:

```rust
impl Race {
    pub fn record_breakers_bf(&self) -> u64 {
        (0..=self.time)
            .filter(|x| x * (self.time - x) > self.record)
            .count() as u64
    }
}

fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, races) = parse::races(&input).unwrap();
    assert_eq!(s.trim(), "");

    let result = races
        .iter()
        .map(|r| r.record_breakers_bf())
        .product::<u64>();

    println!("{result}");
    Ok(())
}
```

I like how compact that code is. 

Running it:

```bash
$ hyperfine 'just run 6 1-brute'

Benchmark 1: just run 6 1-brute
  Time (mean ± σ):     152.3 ms ±  74.5 ms    [User: 35.5 ms, System: 16.8 ms]
  Range (min … max):    82.6 ms … 277.9 ms    11 runs
```

That's fine for now.

## Part 2

> Instead of treating the input as individual values, concatenate each line of input into a single (much larger) value. So instead of times of `7 15 30`, you have one of `71530`. 

Well, here's where we might need to do a bit of optimization. Let's find out!

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, races) = parse::races(&input).unwrap();
    assert_eq!(s.trim(), "");

    let race = Race {
        time: races
            .iter()
            .map(|r| r.time.to_string())
            .collect::<String>()
            .parse::<u64>()?,
        record: races
            .iter()
            .map(|r| r.record.to_string())
            .collect::<String>()
            .parse::<u64>()?,
    };

    let result = race.record_breakers_bf();

    println!("{result}");
    Ok(())
}
```

`.collect::<String>` is neat. :smile: 

How does it run?

```bash
$ just time 6 2-brute

hyperfine 'just run 6 2-brute'
Benchmark 1: just run 6 2-brute
  Time (mean ± σ):     148.4 ms ±  50.6 ms    [User: 51.4 ms, System: 14.2 ms]
  Range (min … max):    99.1 ms … 267.3 ms    11 runs
```

Actually... it's completely fine. I didn't expect that, but I suppose it's still only ~50 million values. 

## (Premature) Optimization 

Okay, time to be honest. I didn't actually write the brute force solution first. I didn't expect it to work *nearly* as well as it did. Instead, I went all quadratic equation on things!

* The race is D units long
* Each option is hold the button for x seconds, maximum of T
* Distance traveled is x for T-x seconds
* We need to travel at least D

{{<latex>}}
x(T-x) > D \\
xT - x^2 > D \\
x^2 - xT + D < 0 \\
x \between \frac{T \pm \sqrt{T^2 - 4D}}{2} \\
{{</latex>}}

In code:

```rust
impl Race {
    pub fn record_breakers(&self) -> u64 {
        // Race is D units long
        // Each option is hold the button for x seconds, maximum of T
        // Distance traveled is x for T-x seconds
        // We need to travel at least D
        // x(T-x) > D
        // xT - x^2 > D
        // x^2 - xT + D < 0
        // x in (T +/- sqrt(T^2 - 4D)) / 2

        let t = self.time as f64;
        let d = self.record as f64;

        let x1 = (t - (t * t - 4.0 * d).sqrt()) / 2.0;
        let x2 = (t + (t * t - 4.0 * d).sqrt()) / 2.0;

        let lo = x1.min(x2).ceil() as u64;
        let hi = x1.max(x2).floor() as u64;

        // If lo is an integer, we don't want it (< vs <=)
        // But it's a float, so check by epsilon difference
        // This isn't perfect, but it works
        let diff = ((lo as f64) - x1.min(x2)).abs();

        if diff < 1e-6 {
            hi - lo - 1
        } else {
            hi - lo + 1
        }
    }
}
```

Then for each solution we can just use `record_breakers` instead of `record_breakers_bf`. But... does it actually help? (There's not *really* much room for optimization).

```bash
$ hyperfine --warmup 3 'just run 6 1' 'just run 6 1-brute'

Benchmark 1: just run 6 1
  Time (mean ± σ):     102.9 ms ±  32.6 ms    [User: 31.4 ms, System: 13.4 ms]
  Range (min … max):    77.1 ms … 196.9 ms    31 runs

Benchmark 2: just run 6 1-brute
  Time (mean ± σ):     115.8 ms ±  32.0 ms    [User: 32.6 ms, System: 13.8 ms]
  Range (min … max):    83.2 ms … 200.9 ms    31 runs

Summary
  just run 6 1 ran
    1.13 ± 0.47 times faster than just run 6 1-brute

$ hyperfine --warmup 3 'just run 6 2' 'just run 6 2-brute'

Benchmark 1: just run 6 2
  Time (mean ± σ):     103.3 ms ±  29.4 ms    [User: 31.8 ms, System: 12.5 ms]
  Range (min … max):    81.4 ms … 167.5 ms    33 runs

Benchmark 2: just run 6 2-brute
  Time (mean ± σ):     120.7 ms ±  27.1 ms    [User: 47.8 ms, System: 12.4 ms]
  Range (min … max):    99.3 ms … 188.4 ms    25 runs

Summary
  just run 6 2 ran
    1.17 ± 0.42 times faster than just run 6 2-brute
```

10% faster (for the mathy version). That's not nothing... but it's pretty close at this scale. I expect a lot of speedup in the direct version is lost by doing `sqrt` and division. 

If we scaled *way* up, perhaps this would matter? It would have to be pretty big though!

Anyways, it was an interesting. Onward!