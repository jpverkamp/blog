---
title: "AoC 2025 Day 8: Point Cloudinator"
date: 2025-12-08 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 8: Playground](https://adventofcode.com/2025/day/8)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day8.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a list of points in 3D space, connect the 1000 closest nodes to each other. Calculate the product of the size of the 3 largest resulting regions? 

<!--more-->

I feel like there should be a better way to do this... but honestly, I can't find it. I went down the [[wiki:octree]]() rabbit hole for a while.

So instead, let's just do it. Calculate *all the distances*, sort them, apply the first 1000, calculate region sizes. 

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let mut lines = input.lines().peekable();

    // The test cases is shorter, so if there's a # on the first line, use that
    let join_count = if lines.peek().unwrap().starts_with('#') {
        lines.next().unwrap()[1..].trim().parse::<usize>().unwrap()
    } else {
        1000
    };

    // Parse points
    let points = lines.map(Point3D::from).collect::<Vec<_>>();
    let points_len = points.len();

    // Initialize each point to be its own region
    let mut regions = (0..points_len).collect::<Vec<_>>();

    // Pre-calculate and sort all distances
    // This seems excessive, but I'm not sure you can avoid it...
    let mut distances = vec![];
    for i in 0..points_len {
        for j in i + 1..points.len() {
            distances.push((points[i].distance_squared(&points[j]), (i, j)));
        }
    }
    distances.sort_by_key(|(d, _)| *d);

    // For the first n distances, join them
    let mut distances = distances.iter();
    for _i in 0..join_count {
        let (_, (i, j)) = distances.next().unwrap();

        let region_to_keep = regions[*i];
        let region_to_replace = regions[*j];
        for region in regions.iter_mut() {
            if *region == region_to_replace {
                *region = region_to_keep;
            }
        }
    }

    // Calculate the size of each region, the answer is the product of the largest 3
    sorted((0..points_len).map(|region_id| regions.iter().filter(|r| **r == region_id).count()))
        .rev()
        .take(3)
        .product::<usize>()
        .to_string()
}
```

That just feels wrong.

```bash
$ just run-and-bench 8 part1

90036

part1: 16.773309ms ± 3.254843ms [min: 15.745209ms, max: 46.466042ms, median: 16.206542ms]
```

But it's reasonably performant? I do miss that little µ. 

## Part 2

> Continue iterating until all nodes are part of the same region. What is the product of the `x` of the final two points joined? 

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let mut lines = input.lines().peekable();

    // We don't care about iteration count
    if lines.peek().unwrap().starts_with('#') {
        lines.next();
    }

    // Parse points
    let points = lines.map(Point3D::from).collect::<Vec<_>>();
    let points_len = points.len();

    // Initialize each point to be its own region
    let mut regions = (0..points_len).collect::<Vec<_>>();

    // Pre-calculate and sort all distances
    // This seems excessive, but I'm not sure you can avoid it...
    let mut distances = vec![];
    for i in 0..points_len {
        for j in i + 1..points.len() {
            distances.push((points[i].distance_squared(&points[j]), (i, j)));
        }
    }
    distances.sort_by_key(|(d, _)| *d);

    // For the first n distances, join them
    let mut distances = distances.iter();
    loop {
        let (_, (i, j)) = distances.next().unwrap();
        if regions[*i] == regions[*j] {
            continue;
        }

        let region_to_keep = regions[*i];
        let region_to_replace = regions[*j];
        for region in regions.iter_mut() {
            if *region == region_to_replace {
                *region = region_to_keep;
            }
        }

        // If there's only one region, we're done
        // The answer is the product of the two points' x
        if regions.iter().all(|r| *r == region_to_keep) {
            return (points[*i].x * points[*j].x).to_string();
        }
    }
}
```

Only a minor rewrite (mostly the `loop` condition). 

```bash
$ just run-and-bench 8 part2

6083499488

part2: 16.645156ms ± 449.537µs [min: 15.710708ms, max: 17.517792ms, median: 16.664083ms]
```

Amusing it's basically the same runtime. I wonder just how much of the runtime is spent parsing and calculating all the distances. 

## Part 1 - Binary Heap

One thing you can do to make it a bit faster is to use a [[wiki:Binary Heap]]() rather than sorting. Basically, this let's us only 'sort' the first bit of it. Slightly better:

```rust
// ...

    // Pre-calculate and sort all distances
    // This seems excessive, but I'm not sure you can avoid it...
    let mut distances = BinaryHeap::new();
    for i in 0..points_len {
        for j in i + 1..points.len() {
            distances.push((-points[i].distance_squared(&points[j]), (i, j)));
        }
    }

    
    // For the first n distances, join them
    for _i in 0..join_count {
        let (_, (i, j)) = distances.pop().unwrap();

//...
```

Slightly better:

```bash
$ just run-and-bench 8 part1_heap

90036

part1_heap: 7.8063ms ± 206.49µs [min: 7.463625ms, max: 8.471375ms, median: 7.748459ms]
```

## Benchmarks

```bash
$ just bench 8

part1: 16.634383ms ± 418.086µs [min: 15.914833ms, max: 17.943458ms, median: 16.613125ms]
part2: 16.977939ms ± 497.608µs [min: 16.027458ms, max: 17.93675ms, median: 17.061291ms]
```

| Day | Part | Solution     | Benchmark               |
| --- | ---- | ------------ | ----------------------- |
| 8   | 1    | `part1`      | 16.634383ms ± 418.086µs |
| 8   | 1    | `part1_heap` | 8.19521ms ± 314.775µs   |
| 8   | 2    | `part2`      | 16.977939ms ± 497.608µs |