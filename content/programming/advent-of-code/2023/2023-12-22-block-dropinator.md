---
title: "AoC 2023 Day 22: Block Dropinator"
date: 2023-12-22 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 22: Sand Slabs](https://adventofcode.com/2023/day/22)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day22) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a series of 3D blocks, allow them to fall until the simulation is stable. Any cube of a block is sufficient to support another block, ignore rotations etc. 
>
> How many blocks are not the sole supporter for any other block?

<!--more-->

### Types and Parsing

This one sounds like a fun one to simulate!

First, a (3D!) `Point` and `Block`:

```rust
#[derive(Debug, Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Point {
    pub x: isize,
    pub y: isize,
    pub z: isize,
}

impl Point {
    pub fn new(x: isize, y: isize, z: isize) -> Self {
        Self { x, y, z }
    }

    pub fn manhattan_distance(&self, other: &Self) -> isize {
        (self.x - other.x).abs() + (self.y - other.y).abs() + (self.z - other.z).abs()
    }
}

#[derive(Debug, Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Block {
    pub min: Point,
    pub max: Point,
}

impl Block {
    pub fn new(min: Point, max: Point) -> Self {
        Self { min, max }
    }

    pub fn contains(&self, point: Point) -> bool {
        self.min.x <= point.x
            && self.min.y <= point.y
            && self.min.z <= point.z
            && self.max.x >= point.x
            && self.max.y >= point.y
            && self.max.z >= point.z
    }

    pub fn intersects(&self, other: &Self) -> bool {
        self.min.x <= other.max.x
            && self.min.y <= other.max.y
            && self.min.z <= other.max.z
            && self.max.x >= other.min.x
            && self.max.y >= other.min.y
            && self.max.z >= other.min.z
    }
}

impl std::ops::Add<Point> for Block {
    type Output = Self;

    fn add(self, rhs: Point) -> Self::Output {
        Self {
            min: Point::new(self.min.x + rhs.x, self.min.y + rhs.y, self.min.z + rhs.z),
            max: Point::new(self.max.x + rhs.x, self.max.y + rhs.y, self.max.z + rhs.z),
        }
    }
}
```

[Copilot](https://github.com/features/copilot) is kind of great for writing unit tests for things like this. :smile:

I'm not at all validating that `min` is actually the 'minimum' corner or that `max` is the maximum, but that's the case for this input. 

Now parse it:

```rust
fn point(input: &str) -> IResult<&str, Point> {
    map(
        tuple((
            complete::i64,
            delimited(complete::char(','), complete::i64, complete::char(',')),
            complete::i64,
        )),
        |(x, y, z)| Point::new(x as isize, y as isize, z as isize),
    )(input)
}

fn block(input: &str) -> IResult<&str, Block> {
    map(
        separated_pair(point, complete::char('~'), point),
        |(min, max)| Block::new(min, max),
    )(input)
}

pub fn blocks(input: &str) -> IResult<&str, Vec<Block>> {
    separated_list1(line_ending, block)(input)
}
```

Nice!

### Solution

Okay, this is a bit longer:

```rust
fn main() -> Result<()> {
    env_logger::init();

    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (s, mut blocks) = parse::blocks(&input).unwrap();
    assert!(s.trim().is_empty());

    let gravity: Point = Point::new(0, 0, -1);

    log::info!("Dropping blocks");
    for step in 0.. {
        log::info!("- Step {}", step);
        let mut updated = false;

        for i in 0..blocks.len() {
            // Cannot fall through the floor
            if blocks[i].min.z == 1 {
                continue;
            }

            // Cannot fall through another block
            let fallen = blocks[i] + gravity;
            if blocks
                .iter()
                .enumerate()
                .any(|(j, block)| i != j && block.intersects(&fallen))
            {
                continue;
            }

            // If we've made it this far, drop the block and mark updated
            blocks[i] = fallen;
            updated = true;
        }

        if !updated {
            break;
        }
    }

    log::info!("Calculating supports");
    let supported_by = blocks
        .iter()
        .map(|block| {
            (
                block,
                blocks
                    .iter()
                    .filter(|other| block != *other && (*block + gravity).intersects(other))
                    .collect::<Vec<_>>(),
            )
        })
        .collect::<Vec<_>>();

    let block_name = |block: &Block| -> String {
        let index = blocks.iter().position(|b| b == block).unwrap();
        if index <= 26 {
            format!("{}({index})", (b'A' + index as u8) as char)
        } else if index <= 52 {
            format!("{}({index})", (b'a' + index as u8) as char)
        } else {
            format!("{index}")
        }
    };

    log::info!("Supported blocks:");
    for (block, supported_by) in supported_by.iter() {
        let name = block_name(block);
        log::info!("- Block {name}: {block:?}");
        for other in supported_by.iter() {
            let name = block_name(other);
            log::info!("  - {name}: {other:?}");
        }
    }

    // Safe blocks are those that never are the only support for any other block
    let result = blocks
        .iter()
        .filter(|block| {
            !supported_by
                .iter()
                .any(|(_, supports)| supports.contains(block) && supports.len() == 1)
        })
        .count();

    println!("{result}");
    Ok(())
}
```

I've left in my `log::info!` statements as they're essentially what I would otherwise have commented there to remember what each section does. 

The algorithm is:

* Loop until blocks stop falling:
  * For each block, try to drop it one unit--if it doesn't hit anything
* Calculate supports
  * For each block, it's supports are the set of blocks that if you fell one block you would hit
* Calculate the result: 'safe' blocks are those that never appear as the only block in the `supported_by` data structure

I think that's fairly elegant!

## Part 2

> For each block, count how many blocks would fall if that block were removed (including transitively). Sum these numbers. 

### 

That's actually a pretty fascinating problem--that I think is made at least doable by how we've calculated `supported_by`. My plan of attack:

* For each block `b`:
  * Create a new copy of `supported_by` that we're going to mutate
  * Until the simulation is stable:
    * Remove* `b` from `supported_by`
    * Find any blocks that are unsupported (not on the ground and with no more blocks in their `supported_by` sublist)
      * Remove those
  * Count how many blocks are left, this tells you how many fell

In code:

```rust
fn main() -> Result<()> {
    // ... same as part 1 ...

    // A helper function to remove blocks from a supported_by structure
    // This will remove the block from each sublist and the main list
    fn remove_from_supports(supported_by: &mut Vec<(&Block, Vec<&Block>)>, block: &Block) {
        supported_by.iter_mut().for_each(|supports| {
            let index = supports.1.iter().position(|b| *b == block);
            if let Some(index) = index {
                supports.1.remove(index);
            }
        });

        let index = supported_by.iter().position(|(b, _)| *b == block).unwrap();
        supported_by.remove(index);
    }

    let result = blocks
        .iter()
        .map(|block| {
            let name = block_name(block);
            log::info!("Attempting to remove {name}: {block:?}");

            // Make a local copy of supported blocks
            let mut supported_by = supported_by.clone();

            // Remove that block from any supports
            let name = block_name(block);
            log::info!("- Removing {name}: {block:?}");
            remove_from_supports(&mut supported_by, block);

            // Repeatedly remove blocks that are unsupported
            log::info!("- Settling unsupported blocks");
            loop {
                let mut changed = false;

                // Find blocks that are now unsupported (and not on the floor)
                let to_remove = supported_by
                    .iter()
                    .filter(|(block, supports)| block.min.z > 1 && supports.is_empty())
                    .map(|(block, _)| **block)
                    .collect::<Vec<_>>();

                for block in to_remove.iter() {
                    let name = block_name(block);
                    log::info!("  - Removing {name}: {block:?}");

                    remove_from_supports(&mut supported_by, block);
                    changed = true;
                }

                if !changed {
                    break;
                }
            }

            // Return the number of blocks that were removed
            // Off by 1 because the original 'block' doesn't count as fallen
            blocks.len() - supported_by.len() - 1
        })
        .sum::<usize>();

    println!("{result:?}");
    Ok(())
}
```

And... that just works!  There was a bit of fiddling with `.iter()` vs `loops` when it came to Rust's borrow checker (and the `remove_from_supports` function is a bit weird, but [we'll come back to that](#trying-other-datatypes)). But I think it's fairly elegant, all things considered. 

### Trying other datatypes

One downside to all this is that... it's a bit slow. I mean, it's only 2 seconds, but I think we could possibly do a bit better? 

One place that we have room for improvement is in our choice of data structures. 

Currently `supported_by`, which we're constantly removing elements from is a `Vec<(Block, Vec<Block>)>`. But it doesn't have to be! 

What if we used a `FxHashMap` for the outer level? Actually all that has to change is the initial `supported_by` becomes `.collect::<FxHashMap<_, _>>();` and `remove_from_supports` becomes:

```rust
fn remove_from_supports(supported_by: &mut FxHashMap<&Block, Vec<&Block>>, block: &Block) {
    supported_by.iter_mut().for_each(|supports| {
        let index = supports.1.iter().position(|b| *b == block);
        if let Some(index) = index {
            supports.1.remove(index);
        }
    });

    supported_by.remove(block);
}
```

(The last line is just a straight `remove`). That should give us quicker lookups and removals. 

Or we can go one step further! Make it `FxHashMap<Block, FxHashSet<Block>>`? We just need to change the inner `collect` to `.collect::<FxHashSet<_>>()` and clean up `remove_from_supports` a bit more:

```rust
fn remove_from_supports(
    supported_by: &mut FxHashMap<&Block, FxHashSet<&Block>>,
    block: &Block,
) {
    supported_by.values_mut().for_each(|supports| {
        supports.remove(block);
    });

    supported_by.remove(block);
}
```

I actually really like how much cleaner this made this code if nothing else. 

So... how is performance? 

```bash
$ hyperfine --warmup 3 'just run 22 2-vec-vec' 'just run 22 2-hash-vec' 'just run 22 2-hash-set'

Benchmark 1: just run 22 2-vec-vec
  Time (mean ± σ):      2.049 s ±  0.113 s    [User: 1.835 s, System: 0.020 s]
  Range (min … max):    1.939 s …  2.208 s    10 runs

Benchmark 2: just run 22 2-hash-vec
  Time (mean ± σ):      2.048 s ±  0.060 s    [User: 1.899 s, System: 0.021 s]
  Range (min … max):    2.009 s …  2.212 s    10 runs

Benchmark 3: just run 22 2-hash-set
  Time (mean ± σ):      1.959 s ±  0.041 s    [User: 1.808 s, System: 0.023 s]
  Range (min … max):    1.933 s …  2.072 s    10 runs

  Warning: Statistical outliers were detected. Consider re-running this benchmark on a quiet system without any interferences from other programs. It might help to use the '--warmup' or '--prepare' options.

Summary
  just run 22 2-hash-set ran
    1.05 ± 0.04 times faster than just run 22 2-hash-vec
    1.05 ± 0.06 times faster than just run 22 2-vec-vec
```

All that for a 5% speedup? I mean, it's not terrible and it got us under the 2 second mark at least. But I expected more. Really though, we're at the scale (~1500 blocks) where the cost of hashing and collisions probably outweighs the gains. Scanning through a (shrinking) ~1500 elements is pretty quick. 

So it goes. 

### Remove debugging

Another option would be to completely remove all of the `log::info!` lines and thus the `block_name` function. That should buy us something, since we're not creating strings (that we don't even use without `RUST_LOG=info`). 

Luckily, it seems Rust's compiler is pretty smart anyways, this only saves us ~1/100 of a second more. So we'll leave it in. 

## Performance

With the tweaks above, we have:

```bash
$ just time 22 1

hyperfine --warmup 3 'just run 22 1'
Benchmark 1: just run 22 1
  Time (mean ± σ):      1.376 s ±  0.015 s    [User: 1.264 s, System: 0.016 s]
  Range (min … max):    1.356 s …  1.404 s    10 runs

$ just time 22 2

hyperfine --warmup 3 'just run 22 2'
Benchmark 1: just run 22 2
  Time (mean ± σ):      1.783 s ±  0.049 s    [User: 1.651 s, System: 0.021 s]
  Range (min … max):    1.739 s …  1.902 s    10 runs
```

Come to think of it, our runtime is actually 2/3 in `part1`... I bet we could speed that up. Another day though. 

Onward!