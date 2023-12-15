---
title: "AoC 2023 Day 15: Hashinator"
date: 2023-12-15 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 15: Lens Library](https://adventofcode.com/2023/day/15)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day15) for today (spoilers!)

{{<toc>}}

## Part 1

> Hash each input (comma separated) with `h(v, c) = (v + c) * 17` (modulo 256 / as a byte). Sum these values. 

<!--more-->

So... I'm not even going to make types or parse this. I know right? 

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    fn hash(s: &str) -> u8 {
        s.chars()
            .fold(0, |v, c| ((v.wrapping_add(c as u8)).wrapping_mul(17)))
    }

    let result = input
        .split(',')
        .map(hash)
        .map(|v| v as usize)
        .sum::<usize>();

    println!("{result}");
    Ok(())
}
```

The most interesting part perhaps is using `wrapping_(add|mul)` to tell the compiler what I want done with overflow. Rust protecting me from myself :smile:. 

## Part 2

> Implement a [[wiki:hashmap]](). More specifically, for input `key-`, remove `key` (if it exists) from the hashmap. For `key=value`, update or insert `key=value` into the hashmap.
>
> Calculate the product of box index, index within box, and value (using 1 based indexing). 

I could certainly formalize this more... but again, not going to!

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    fn hash(s: &str) -> u8 {
        s.chars()
            .fold(0, |v, c| ((v.wrapping_add(c as u8)).wrapping_mul(17)))
    }

    let mut boxes: Vec<Vec<(&str, u8)>> = (0..256).map(|_| vec![]).collect::<Vec<_>>();

    input.split(',').for_each(|s| {
        if s.ends_with('-') {
            // Remove (if exists)
            let s = s.strip_suffix('-').unwrap();
            let k = hash(s) as usize;
            if let Some(i) = boxes[k].iter().position(|b| b.0 == s) {
                boxes[k].remove(i);
            }
        } else {
            // Assuming the only other case is =
            // Update (if exists) or insert (if not)
            let (s, v) = s.split_once('=').unwrap();
            let k = hash(s) as usize;
            let v = v.parse::<u8>().unwrap();

            if let Some(i) = boxes[k].iter().position(|b| b.0 == s) {
                boxes[k][i] = (s, v);
            } else {
                boxes[k].push((s, v));
            }
        }
    });

    let result = boxes
        .iter()
        .enumerate()
        .map(|(i, b)| {
            b.iter()
                .enumerate()
                .map(|(j, (_, v))| (i + 1) * (j + 1) * (*v as usize))
                .sum::<usize>()
        })
        .sum::<usize>();

    println!("{result}");

    Ok(())
}
```

`boxes` is a `Vec<Vec<(key, value)>>`. This could easily be a slice directly for the outer one, since we know the size, but performancewise, it's basically the same in Rust so long as you're not resizing things. 

The `for_each` has all of the logic. Calculate the key and `remove`, `update`, or `insert` depending on what you find. 

After that, sum them up (with a bunches of indexes in the mix) and away we go!

## Performance

```bash
$ just time 15 1

hyperfine --warmup 3 'just run 15 1'
Benchmark 1: just run 15 1
  Time (mean ± σ):      80.0 ms ±   4.2 ms    [User: 30.4 ms, System: 11.6 ms]
  Range (min … max):    76.0 ms …  91.0 ms    34 runs

$ just time 15 2

hyperfine --warmup 3 'just run 15 2'
Benchmark 1: just run 15 2
  Time (mean ± σ):      80.1 ms ±   3.1 ms    [User: 30.7 ms, System: 12.0 ms]
  Range (min … max):    76.2 ms …  89.3 ms    33 runs
```

I expect most of that time is disk access. 

Actually... 

```rust
let now = std::time::Instant::now();

// ... code goes here ...

println!("{:?}", now.elapsed());
```

...gives...

```bash
$ just run 15 1

cat data/$(printf "%02d" 15).txt | cargo run --release -p day$(printf "%02d" 15) --bin part1
    Finished release [optimized] target(s) in 0.00s
     Running `target/release/part1`
93.334µs
508552

$ just run 15 2

cat data/$(printf "%02d" 15).txt | cargo run --release -p day$(printf "%02d" 15) --bin part2
    Finished release [optimized] target(s) in 0.00s
     Running `target/release/part2`
244.083µs
265462
```

Yeah... less than 1/10 ms for part 1 and 1/4 for part 2. 

Perhaps I should rethink how I'm timing these. :smile: