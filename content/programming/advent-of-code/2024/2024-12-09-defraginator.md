---
title: "AoC 2024 Day 9: Defraginator"
date: 2024-12-09 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 9: Disk Fragmenter](https://adventofcode.com/2024/day/9)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day9.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a disk layout alternating between files and empty spaces, move all files as early on the disk is possible, splitting into multiple blocks. Return a checksum on the disk. 
>
> Alternating means: `23331` would mean a 2 block file, 3 empty, a 3 block file, 3 empty, and a 1 block file.
>
> The checksum is the sum of `file_id * block_index` for all occupied blocks. File IDs are assigned sequentially on initial generation. 

<!--more-->

Okay, let's define and load a `Disk`. I'm going to keep a `Vec<Block>` as the main data structure. This has the upside of simplicity and cache friendliness, but has the downside that if we have very large files, there will be a lot of wasted space. 

...but we already know that no file can take up more than `9` blocks, since they're only defined as numbers `1..=9`. 

```rust
#[derive(Debug, Clone, Copy, Default)]
enum Block {
    #[default]
    Empty,
    File(usize),
}

#[derive(Debug, Clone, Copy, Default)]
struct File {
    start: usize,
    size: usize,
}

#[derive(Debug, Clone)]
struct Disk {
    blocks: Vec<Block>,
    files: Vec<File>,
}

impl From<&str> for Disk {
    fn from(input: &str) -> Self {
        let mut blocks = vec![];
        let mut files = vec![];

        let mut next_index = 0;
        let mut next_is_file = true;

        for c in input.chars() {
            if !c.is_ascii_digit() {
                continue;
            }

            let v = c.to_digit(10).unwrap() as usize;
            if next_is_file {
                files.push(File {
                    start: blocks.len(),
                    size: v,
                });
                for _ in 0..v {
                    blocks.push(Block::File(next_index));
                }
                next_index += 1;
            } else {
                for _ in 0..v {
                    blocks.push(Block::Empty);
                }
            }
            next_is_file = !next_is_file;
        }

        Disk { blocks, files }
    }
}
```

I do keep a bit of metadata for `files` as well. For each `id`, you have the `start` of the file (initially) and the `size` of the file in blocks. 

Okay, next up, let's write up the algorithm itself:

```rust
#[aoc(day9, part1, v1)]
fn part1_v1(input: &str) -> usize {
    let mut disk = Disk::from(input);
    let mut left_index = 0;
    let mut right_index = disk.blocks.len() - 1;

    while left_index < right_index {
        // Right index should always point at a file node
        match disk.blocks[right_index] {
            Block::Empty => {
                right_index -= 1;
                continue;
            }
            Block::File { .. } => {}
        }

        // If left index is empty, swap the right index into it
        // Otherwise, advance
        match disk.blocks[left_index] {
            Block::Empty => {
                disk.blocks.swap(left_index, right_index);
                left_index += 1;
                right_index -= 1;
            }
            Block::File(id) => {
                left_index += disk.files[id].size;
            }
        }
    }

    disk.checksum()
}
```

This is basically running two counters, one from the left looking for the next empty space and one from the right, looking for the next block to move. That's it!

We do need a checksum though:

```rust
impl Disk {
    fn checksum(&self) -> usize {
        self.blocks
            .iter()
            .enumerate()
            .map(|(i, b)| match b {
                Block::Empty => 0,
                Block::File(id) => i * id,
            })
            .sum()
    }
}
```

And that's it for part 1!

```bash
$ cargo aoc --day 9 --part 1

AOC 2024
Day 9 - Part 1 - v1 : 6201130364722
	generator: 42ns,
	runner: 626.458µs
```

Sub millisecond.

As an extra bonus, I did render this one:

<video controls src="/embeds/2024/aoc/day9-part1.mp4" width="100%"></video>

These are always fun to watch. 

## Part 2

> This ends up fragmenting files. Instead, move each file (from highest to lowest ID, so right to left in initial order) to the leftmost space that is large enough to fit the entire file. 

```rust
#[aoc(day9, part2, v1)]
fn part2_v1(input: &str) -> usize {
    let mut disk = Disk::from(input);

    // We're going to try to move each file from right to left exactly once
    'each_file: for moving_id in (0..disk.files.len()).rev() {
        // TODO: We can probably cache the leftmost empty block to start at
        let mut left_index = 0;
        let mut empty_starts_at = None;

        while left_index < disk.files[moving_id].start {
            match disk.blocks[left_index] {
                Block::File(_) => {
                    left_index += 1;
                    empty_starts_at = None;
                }
                Block::Empty => {
                    if empty_starts_at.is_none() {
                        empty_starts_at = Some(left_index);
                    }

                    // Found a large enough space
                    if empty_starts_at.is_some_and(|empty_starts_at| {
                        left_index - empty_starts_at + 1 >= disk.files[moving_id].size
                    }) {
                        for i in 0..disk.files[moving_id].size {
                            disk.blocks.swap(
                                disk.files[moving_id].start + i,
                                empty_starts_at.unwrap() + i,
                            );
                        }
                        disk.files[moving_id].start = empty_starts_at.unwrap();
                        continue 'each_file;
                    } else {
                        left_index += 1;
                    }
                }
            }
        }
    }

    disk.checksum()
}
```

So that's a chunk more code. Most of it comes from having to find a large enough space to fit the entire file. As soon as we do though, we move the file the same way as before: block by block. It seems wrong... but for the moment, it's pretty quick. 

```bash
$ cargo aoc --day 9 --part 2

AOC 2024
Day 9 - Part 2 - v1 : 6221662795602
	generator: 42ns,
	runner: 119.026458ms
```

### Optimization (attempt) 1: BTree representation

Okay, let's actually try it. Rather than representing each block in a `Vec`, let's make a `BTreeMap` of `index -> Node` where `Node` is either empty space or a file.

```rust
#[derive(Debug, Clone, Copy)]
enum BTreeBlock {
    Empty { size: usize },
    File { id: usize, size: usize },
}

#[derive(Debug, Clone)]
struct BTreeDisk {
    blocks: BTreeMap<usize, BTreeBlock>,
}

impl From<&str> for BTreeDisk {
    fn from(input: &str) -> Self {
        let mut data = BTreeMap::new();

        let mut next_index = 0;
        let mut next_is_file = true;
        let mut next_file_id = 0;

        for c in input.chars() {
            if c.is_ascii_digit() {
                let size = c.to_digit(10).unwrap() as usize;
                if next_is_file {
                    data.insert(
                        next_index,
                        BTreeBlock::File {
                            id: next_file_id,
                            size,
                        },
                    );
                    next_file_id += 1;
                } else {
                    data.insert(next_index, BTreeBlock::Empty { size });
                }

                next_index += size;
                next_is_file = !next_is_file;
            }
        }

        BTreeDisk { blocks: data }
    }
}
```

It's at least a little easier to load. 

Does it make the actual algorithm any better?

```rust
#[aoc(day9, part2, btree)]
fn part2_btree(input: &str) -> usize {
    let mut disk = BTreeDisk::from(input);

    // Collect the starting start index of each file
    let files = disk
        .blocks
        .iter()
        .filter_map(|(i, block)| match block {
            BTreeBlock::File { size, .. } => Some((*i, *size)),
            _ => None,
        })
        .collect::<Vec<_>>();

    // Try to move each file exactly once, from right to left
    for (_, &(file_start, file_size)) in files.iter().enumerate().rev() {
        // Find the first empty space we can that will fit it
        let empty_index = disk.blocks.iter().find(|(_, block)| match block {
            BTreeBlock::Empty { size } => size >= &file_size,
            _ => false,
        });

        // No blocks that fit it
        if empty_index.is_none() {
            continue;
        }
        let (&empty_index, _) = empty_index.unwrap();

        // Only move left
        if empty_index >= file_start {
            continue;
        }

        let removed_empty_node = disk.blocks.remove(&empty_index).unwrap();
        let removed_file_node = disk.blocks.remove(&file_start).unwrap();

        disk.blocks.insert(empty_index, removed_file_node);
        disk.blocks
            .insert(file_start, BTreeBlock::Empty { size: file_size });

        // If we have extra empty space, insert a new empty node
        match (removed_empty_node, removed_file_node) {
            (
                BTreeBlock::Empty { size: empty_size },
                BTreeBlock::File {
                    id: _,
                    size: file_size,
                },
            ) if empty_size > file_size => {
                disk.blocks.insert(
                    empty_index + file_size,
                    BTreeBlock::Empty {
                        size: empty_size - file_size,
                    },
                );
            }
            _ => {}
        }

        // While we have two neighboring empty nodes, combine them
        loop {
            // There are empty consecutive blocks at a and b
            let maybe_empties = disk.blocks.iter().zip(disk.blocks.iter().skip(1)).find_map(
                |((index, block), (next_index, next_block))| match (block, next_block) {
                    (BTreeBlock::Empty { size: size1 }, BTreeBlock::Empty { size: size2 }) => {
                        Some((*index, *next_index, size1 + size2))
                    }
                    _ => None,
                },
            );

            if let Some((a, b, size)) = maybe_empties {
                disk.blocks.remove(&a);
                disk.blocks.remove(&b);
                disk.blocks.insert(a, BTreeBlock::Empty { size });
            } else {
                // No more consecutive empty blocks
                break;
            }
        }
    }

    disk.checksum()
}
```

I actually think that's a fair bit uglier. There are more edge cases to deal with and we don't actually gain much finding the first empty block. 

And the checksum isn't even any better:

```rust
impl BTreeDisk {
    fn checksum(&self) -> usize {
        self.blocks
            .iter()
            .map(|(&index, &b)| match b {
                BTreeBlock::Empty { .. } => 0,
                BTreeBlock::File { id, size } => {
                    // TODO: We should be able to calculate this directly
                    // id * (2 * index + size) * (size - 1) / 2
                    ((index)..(index + size)).map(|i| i * id).sum::<usize>()
                }
            })
            .sum()
    }
}
```

So how does it perform?

```bash
$ cargo aoc --day 9 --part 2

AOC 2024
Day 9 - Part 2 - v1 : 6221662795602
	generator: 42ns,
	runner: 119.026458ms

Day 9 - Part 2 - btree : 6221662795602
	generator: 11.084µs,
	runner: 929.480416ms
```

All righty then! I suppose we don't need that after all. 

I think this does show off one slight annoyance with the `cargo-aoc` set up. You can't really have two different data structures and still use their `generate` code. At least not easily. I expect you could if you used an `enum`. 

## Optimization 2: Track the leftmost empty space

I rendered this one as well (using the original version):

<video controls src="/embeds/2024/aoc/day9-part2-original.mp4" width="100%"></video>

If you watch to the end, you'll start to notice something a bit strange. It's getting slower and slower to update each file location.

To fix this, all we have to do is make sure that we start the search for new empty blocks to the left:

```rust
#[aoc(day9, part2, leftmost_empty)]
fn part2_leftmost_empty(input: &str) -> usize {
    let mut disk = Disk::from(input);
    let mut leftmost_empty = 0;

    // We're going to try to move each file from right to left exactly once
    'each_file: for moving_id in (0..disk.files.len()).rev() {
        // Advance the leftmost empty block
        // This will be cached so we ignore already filled parts of the drive
        while leftmost_empty < disk.blocks.len() && disk.blocks[leftmost_empty] != Block::Empty {
            leftmost_empty += 1;
        }

        ...
```

<video controls src="/embeds/2024/aoc/day9-part2.mp4" width="100%"></video>

Much smoother!

Doesn't actually impact performance though unfortunately. 

```bash
$ cargo aoc bench --day 9 --part 2

Day9 - Part2/v1             time:   [113.13 ms 113.40 ms 113.70 ms]
Day9 - Part2/leftmost_empty time:   [114.89 ms 115.25 ms 115.69 ms]
```

If anything, it's slower. 

Which is because scanning from the front to find an empty space is actually plenty fast. It's mostly a bug in the rendering... I generate a potential frame on each index scanning, so of course that's going to be slower. 

So it goes!

## Benchmarks

```bash
$ cargo aoc bench --day 9

Day9 - Part1/v1         time:   [384.69 µs 386.91 µs 389.41 µs]
Day9 - Part2/v1         time:   [115.96 ms 117.00 ms 118.18 ms]
Day9 - Part2/btree      time:   [884.94 ms 886.85 ms 888.92 ms]
```