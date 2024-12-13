---
title: "AoC 2024 Day 12: Edginator"
date: 2024-12-12 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
---
## Source: [Day 12: Garden Groups](https://adventofcode.com/2024/day/12)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day12.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a `Grid` of regions, calculate the sum of the product `perimeter * area` for each region. 

<!--more-->

Okay, we can load it as a `Grid`, but we're going to need two new bits of code to actually get the regions. 

First, the code that will scan across the input and for each (unassigned) point, find all connected points to it (and mark them all as assigned so we get each region once):

```rust
#[aoc_generator(day12)]
fn parse(input: &str) -> Grid<char> {
    Grid::read(input, &|c| c)
}

pub fn get_regions<T>(input: &Grid<T>) -> Vec<(&T, Vec<Point>)>
where
    T: Clone + Default + PartialEq,
{
    let mut assigned_regions = Grid::new(input.width, input.height);
    let mut regions = vec![];

    // Calculate the points in each region
    for x in 0..(input.width) {
        for y in 0..(input.height) {
            let p: Point = (x, y).into();

            if assigned_regions.get(p).is_some_and(|v| *v) {
                continue;
            }

            let c = input.get(p).unwrap();

            let region = input.flood_fill(p);
            for p in region.iter() {
                assigned_regions.set(*p, true);
            }
            regions.push((c, region));
        }
    }

    regions
}
```

That of course requires we extend `Grid` with `flood_fill`:

```rust
impl<T> Grid<T>
where
    T: PartialEq + Clone + Default,
{
    pub fn flood_fill(&self, p: impl Into<Point>) -> Vec<Point> {
        let p = p.into();

        if !self.in_bounds(p) {
            return Vec::new();
        }

        let target = self.data[self.index(&p)].clone();

        let mut stack = vec![p];
        let mut visited = vec![false; self.data.len()];
        let mut result = Vec::new();

        while let Some(p) = stack.pop() {
            if !self.in_bounds(p) {
                continue;
            }

            if self.get(p) != Some(&target) {
                continue;
            }

            let index = self.index(&p);

            if visited[index] {
                continue;
            }

            visited[index] = true;

            result.push(p);

            stack.push(p + Point::new(1, 0));
            stack.push(p + Point::new(-1, 0));
            stack.push(p + Point::new(0, 1));
            stack.push(p + Point::new(0, -1));
        }

        result
    }
}
```

It's a different block, since this does require the `T` to be `PartialEq` where most of the `impl<T> Grid<T>` does not. It's really neat how Rust templated `impl` can have different requirements. So you can use this method if you are `PartialEq`, but you don't need to be `PartialEq` to just `.get` or `.set`. 

Once we have that, we know enough to solve the problem:

```rust
#[aoc(day12, part1, v1)]
fn part1_v1(input: &Grid<char>) -> usize {
    let regions = get_regions(input);

    // For each region, find the perimeter, area, and then the score
    regions
        .iter()
        .map(|(&c, region)| {
            // For each point, each neighbor which doesn't match is an edge
            // Score is area times this perimeter
            region.len()
                * region
                    .iter()
                    .map(|p| {
                        p.neighbors()
                            .iter()
                            .map(|n| {
                                if let Some(&v) = input.get(*n) {
                                    if v == c {
                                        0
                                    } else {
                                        1
                                    }
                                } else {
                                    1
                                }
                            })
                            .sum::<usize>()
                    })
                    .sum::<usize>()
        })
        .sum::<usize>()
}
```

That nested a bit more than I'd like. The innermost block `p.neighbors()` is doing perimeter detection: for each neighbor of a point, if it's different, that's 1 unit on the perimeter. 

```rust
cargo aoc --day 12 --part 1

AOC 2024
Day 12 - Part 1 - v1 : 1450816
	generator: 43.125µs,
	runner: 910.625µs
```

In case you are curious (I was!) the regions look like this:

{{<figure src="/embeds/2024/aoc/day12.png">}}

We've got both some really big ones and a few tiny little islands. We do also have to deal with regions completely contained within another region. 

## Part 2

> Instead of the perimeter, count the number of edges. 

I've got a sneaky way to do this one:

```rust
#[aoc(day12, part2, edge_detection)]
fn part2_edge_detection(input: &Grid<char>) -> usize {
    let regions = get_regions(input);

    // For each region, find the number of edges, area, and then the score
    regions
        .iter()
        .map(|(&c, region)| {
            // Edges in this version run along the border of the region
            // Score is area times number of edges
            region.len()
                * Direction::all()
                    .iter()
                    .map(|&direction| {
                        // Run edge detection in each direction once per region
                        // This will create a new grid that is true for edges in that direction
                        let mut edges = Grid::new(input.width, input.height);
                        region.iter().for_each(|p| {
                            if input.get(*p + direction).is_none_or(|&v| v != c) {
                                edges.set(*p, true);
                            }
                        });

                        // For edges in that direction, identify 'regions'
                        // Each of those is a single contiguous edge
                        get_regions(&edges).iter().filter(|(&c, _)| c).count()
                    })
                    .sum::<usize>()
        })
        .sum::<usize>()
}
```

We're going to actually re-use and duplicate the region detection for edges! If we make a grid that is `true` for all points that are an 'up' edge then the number of regions is exactly equal to the number of up edges total!

Here's a graphic showing the up/down edges:

{{<figure src="/embeds/2024/aoc/day12-edges-up.png">}}

And the left/right edges:

{{<figure src="/embeds/2024/aoc/day12-edges-right.png">}}

It's somewhat slower, since we're calculating the edges for each region as it's own `Grid`. I expect I could optimize that, but for the moment, we need each edges because it's multiplied by each area.

```bash
$ cargo aoc --day 12 --part 2

AOC 2024
Day 12 - Part 2 - edge_detection : 865662
	generator: 63.959µs,
	runner: 608.089958ms
```

### Optimization 1: Detect corners instead of edges

Okay, that's kind of expensive. Here's a fun math trick: polygons have the same number of sides and edges. So what's a corner? 

Either this:

```text
*x
xC
```

Where `C` is the corner of the region, `x` is anything that's not `C` (including out of bounds), and `*` can be anything (including `C`--in that case we'll have two corners). 

Or this:

```text
xC
CC
```

With the same conditions. 

```rust
#[aoc(day12, part2, corners)]
fn part2_corners(input: &Grid<char>) -> usize {
    let regions = get_regions(input);

    // For each region, find the number of edges, area, and then the score
    regions
        .iter()
        .map(|(_, region)| {
            // There are an equal number of edges and corners
            // Each corner is either:
            //  *x
            //  xC where each x is anything not C and * can be C or not
            // or
            //  xC
            //  CC

            region.len()
                * region
                    .iter()
                    .map(|p| {
                        let me = input.get(*p);
                        let mut count = 0;

                        for xd in [-1, 1].iter() {
                            for yd in [-1, 1].iter() {
                                // *x
                                // xC case

                                // Along the x and y directions match
                                let neighbor_xd = input.get(*p + Point::new(*xd, 0));
                                let neighbor_yd = input.get(*p + Point::new(0, *yd));

                                if me != neighbor_xd && me != neighbor_yd {
                                    count += 1;
                                }

                                // xC
                                // CC case

                                let neighbor_both = input.get(*p + Point::new(*xd, *yd));

                                if me == neighbor_xd && me == neighbor_yd && me != neighbor_both {
                                    count += 1;
                                }
                            }
                        }

                        count
                    })
                    .sum::<usize>()
        })
        .sum::<usize>()
}
```

It's a bit longer, but I think fairly elegant with the comments. One neat trick is that since I keep `me` as an `Option<c>`, we get the border checks (which return `None`) for free. So we loop in the 4 directions (top left, top right, bottom left, bottom right) and check those two cases, counting how many are corners and... we're done!

```bash
$ cargo aoc --day 12 --part 2

AOC 2024
Day 12 - Part 2 - edge_detection : 865662
	generator: 63.959µs,
	runner: 608.089958ms

Day 12 - Part 2 - corners : 865662
	generator: 56.583µs,
	runner: 1.282333ms
```

That is *bonkers* faster. 600x. 

I think the other algorithm is sneakier (edge detection! re-using 'regions' to define edges!), but I like the edges = corners of this one and--when in a programming challenge--it's good to find code that is *both* fast and elegant. 

Heck, I expect this could be done while doing the floodfill to gain even more of a buff... but I think ~1ms is pretty good for now. 

## Benchmarks

```bash
$ cargo aoc bench --day 12

Day12 - Part1/v1                time:   [827.45 µs 829.68 µs 832.26 µs]
Day12 - Part2/edge_detection    time:   [607.70 ms 615.13 ms 626.18 ms]
Day12 - Part2/corners           time:   [1.0763 ms 1.0787 ms 1.0812 ms]
```

That's by far my slowest so far, but still under a second, so we'll go with it for the moment.