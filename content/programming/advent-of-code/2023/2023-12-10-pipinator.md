---
title: "AoC 2023 Day 10: Pipinator"
date: 2023-12-10 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 10: Pipe Maze](https://adventofcode.com/2023/day/10)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day10) for today (spoilers!)

{{<toc>}}

## Part 1

> You are given as input an [[wiki:ASCII art]]() pipe diagram with straight pipes `|-`, right angle turns `LJ7F`, ground `.`, and a start tile `S`. 
> 
> The start tile will be part of a loop of pipes. 
> 
> Find the distance to the furthest connected pipe segment from `S` (or half the length of the loop). 

<!--more-->

### Types and Parsing

Okay, I feel like this is going to be an interesting one! 

First up, some types.

```rust
#[derive(Debug)]
pub struct Map {
    nodes: Vec<Node>,
    start_index: usize,
}

#[derive(Debug, Eq, PartialEq)]
pub struct Node {
    x: isize,
    y: isize,
    value: char,
    neighbor_a_index: Option<usize>,
    neighbor_b_index: Option<usize>,
}
```

We don't actually need to store the `x` and `y` for `Node` (or actually the `value` either, depending on how we parse things), but I think that they'll be handy to have around.

`neighbor_(a|b)_index` will store the two neighbors for each node. They're `Option` because 1) there will be random nodes in the graph that are not part of the loop and 2) the `S`tart node will need to be filled in when we have the rest of the loop. 

Assuming we have all that, we should be able to write a `From<&str>` for `Map`. As was the case in [[AoC 2023 Day 3: Gearinator|day 3]](), `nom` (so far as I can tell) isn't *great* when it comes to parsing grids like this. 

```rust
// Parse a Map from a &str
impl From<&str> for Map {
    fn from(value: &str) -> Self {
        let raw_nodes = value
            .lines()
            .enumerate()
            .flat_map(|(y, line)| {
                line.chars()
                    .enumerate()
                    .filter(|(_, c)| *c != '.')
                    .map(move |(x, value)| (x as isize, y as isize, value))
            })
            .collect::<Vec<_>>();

        let start_index = raw_nodes
            .iter()
            .position(|(_, _, value)| *value == 'S')
            .unwrap();

        fn index_offset(
            raw_nodes: &[(isize, isize, char)],
            x: isize,
            y: isize,
            xd: isize,
            yd: isize,
        ) -> Option<usize> {
            raw_nodes
                .iter()
                .position(|(x2, y2, _)| x + xd == *x2 && y + yd == *y2)
        }

        // Forward is first clockwise from up
        // Backwards is second

        let mut nodes = raw_nodes
            .iter()
            .map(|(x, y, value)| Node {
                x: *x,
                y: *y,
                value: *value,
                neighbor_a_index: match *value {
                    // Up
                    '|' | 'L' | 'J' => index_offset(&raw_nodes, *x, *y, 0, -1),
                    // Right (but no up)
                    '-' | 'F' => index_offset(&raw_nodes, *x, *y, 1, 0),
                    // Down (but not right or up)
                    '7' => index_offset(&raw_nodes, *x, *y, 0, 1),
                    // Left (can't have the first one go only left)
                    // Ignore S (we'll figure this out later)
                    'S' => None,
                    // Break on anything else
                    _ => panic!("Invalid value: {}", value),
                },
                neighbor_b_index: match *value {
                    // Up (can't have the second one go up)
                    // Right (first must have gone up)
                    'L' => index_offset(&raw_nodes, *x, *y, 1, 0),
                    // Down (first must have gone up or right)
                    '|' | 'F' => index_offset(&raw_nodes, *x, *y, 0, 1),
                    // Left (anything else really)
                    '-' | 'J' | '7' => index_offset(&raw_nodes, *x, *y, -1, 0),
                    // Ignore S (we'll figure this out later)
                    'S' => None,
                    // Break on anything else
                    _ => panic!("Invalid value: {}", value),
                },
            })
            .collect::<Vec<_>>();

        // The start node has exactly two neighbors; find them
        let start_neighbors = nodes
            .iter()
            .enumerate()
            .filter_map(|(i, node)| {
                if node.neighbor_a_index.is_some_and(|j| j == start_index)
                    || node.neighbor_b_index.is_some_and(|j| j == start_index)
                {
                    Some(i)
                } else {
                    None
                }
            })
            .collect::<Vec<_>>();
        assert_eq!(start_neighbors.len(), 2);

        nodes[start_index].neighbor_a_index = Some(start_neighbors[0]);
        nodes[start_index].neighbor_b_index = Some(start_neighbors[1]);

        Map { nodes, start_index }
    }
}
```

Okay. That's heavy. Hopefully it's well commented. I really should write better tests though. Essentially, we're going to go through a few phases:

1. Find all of the `raw_nodes` - this is just an `(x, y, c)` for each node, using `enumerate()` to get the indexes and dropping the ground (`.`) nodes
2. Define a helper `index_offset` which will take a list of raw nodes, an `(x, y)` and an `(xd, yd)` offset and find the index (in `raw_nodes`) which nodes (if any) is at that position
3. Another `iter` to build the actual `Nodes`, a lot of the work here is finding the two `neighbor_(a|b)_index` values and making sure that they don't overlap. As mentioned, to do that, I'm specifically defining `a` as the 'first' point starting up and going clockwise and `b` the second--there will be more than two
4. The `S`tart node should now have exactly two neighbors that point to it, fill in index pointers to those two nodes

And that's *it* relatively speaking. Step 3 is definitely a bit error prone, since I had to make sure that I was consistent around which was `a` and which `b` or you get loops. Ask me how I know :smile:. 

### Iterating

The next useful thing to have will be a way to `iter` on a `Map`. Specifically, I want to start at the `start_node` and return each node along the loop exactly once. 

One funny bit here is that you can't just always take the `a` (or `b`) neighbor, because `|` has `a` going up no matter if you'd be going up or down. So to handle this, you have to keep track of both your current position in the iter and where you just came from (if you have a choice where to go, go to the one that *isn't* going backwards):

```rust
// An iterator over the nodes in Map
// Starts at the start node
// Returns each node (on the loop) once
#[derive(Debug, Copy, Clone)]
pub struct MapIterator<'a> {
    map: &'a Map,
    current_index: Option<usize>,
    previous_index: Option<usize>,
    fresh: bool,
}

impl<'a> Iterator for MapIterator<'a> {
    type Item = &'a Node;

    fn next(&mut self) -> Option<Self::Item> {
        // If we manage to run off a trail, something went wrong, but this will stop iter
        self.current_index?;

        // The node we're about to return
        let node = &self.map.nodes[self.current_index.unwrap()];

        // Only return the Start node once
        if !self.fresh && node.value == 'S' {
            return None;
        }

        // Find the next node, if 'a' points to the one we were just at, use 'b' instead
        let mut next_index = node.neighbor_a_index;
        if next_index == self.previous_index {
            next_index = node.neighbor_b_index;
        }
        self.previous_index = self.current_index;
        self.current_index = next_index;
        self.fresh = false;

        Some(node)
    }
}

impl Map {
    pub fn iter(&self) -> MapIterator {
        MapIterator {
            map: self,
            current_index: Some(self.start_index),
            previous_index: None,
            fresh: true,
        }
    }
}
```

### Solution

Okay, that's a lot to get here, but now we should be able to directly calculate the solution using [[wiki:Floyd's tortoise and hare algorithm]](). Essentially, start two `iter` with one moving twice as fast. Eventually, the fast one will catch up to the slow one; that will be the length of the cycle. Half that is our answer. 

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let map = Map::from(input.as_str());

    // Set off two iters, one at double speed
    // Skip the first nyde for each to avoid the start node
    // When they are equal, they have reached the farthest point
    let mut result = map
        .iter()
        .cycle()
        .skip(1)
        .zip(map.iter().cycle().skip(2).step_by(2))
        .position(|(n1, n2)| n1 == n2)
        .unwrap();

    result = (result + 1) / 2;

    println!("{result}");
    Ok(())
}
```

I do enjoy functional Rust sometimes. :smile:

## Part 2

> Calculate the area completely enclosed by the loop containing the `S`tart node. Count extraneous pipe sections, but not those within the main loop. If there are two parallel sections of loop such as `.||.`, a region North and South of that would still be connected. 

This one also took some doing. 

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let map = Map::from(input.as_str());

    let (min_x, min_y, max_x, max_y) = map.bounds();

    // Each region is a hash set of points
    let mut region_cw = HashSet::new();
    let mut region_ccw = HashSet::new();

    let mut outside_cw = false;
    let mut outside_ccw = false;

    // Determine the main loop
    let loop_points = map
        .iter()
        .map(|node| (node.x(), node.y()))
        .collect::<HashSet<_>>();

    // Given a specific start point, flood fill all points into the specific region
    // Do not add points that are:
    // 1 - Part of the loop (points that are set but not part of the loop are fine)
    // 2 - Out of bounds
    // 3 - Already added
    let flood_fill = |region: &mut HashSet<(isize, isize)>, start: (isize, isize)| -> bool {
        let mut stack = vec![start];
        let mut is_outside = false;

        while let Some((x, y)) = stack.pop() {
            // Never add points on the loop
            if loop_points.contains(&(x, y)) {
                continue;
            }

            // Never add points out of bounds
            if x < min_x - 1 || x > max_x + 1 || y < min_y - 1 || y > max_y + 1 {
                is_outside = true;
                continue;
            }

            // Stop if we've already added this point to the region
            if region.contains(&(x, y)) {
                continue;
            }

            // Otherwise, add it and expand
            region.insert((x, y));
            stack.push((x + 1, y));
            stack.push((x - 1, y));
            stack.push((x, y + 1));
            stack.push((x, y - 1));
        }

        is_outside
    };

    // Over each pair of points, determine which side is 'clockwise' and which 'counter-clockwise' from that point
    // Flood fill the approproiate region
    map.iter()
        .zip(map.iter().cycle().skip(1))
        .for_each(|(n1, n2)| {
            let (x1, y1) = (n1.x(), n1.y());
            let (x2, y2) = (n2.x(), n2.y());
            let xd = x2 - x1;
            let yd = y2 - y1;

            match (xd, yd) {
                (0, -1) => {
                    // Up
                    // ...
                    // .2x
                    // .1x
                    // ...
                    (0..=1).for_each(|yd| {
                        outside_cw |= flood_fill(&mut region_cw, (x2 + 1, y2 + yd));
                        outside_ccw |= flood_fill(&mut region_ccw, (x2 - 1, y2 + yd));
                    });
                }
                (1, 0) => {
                    // Right
                    // ....
                    // .12.
                    // .xx.
                    (-1..=0).for_each(|xd| {
                        outside_cw |= flood_fill(&mut region_cw, (x2 + xd, y2 + 1));
                        outside_ccw |= flood_fill(&mut region_ccw, (x2 + xd, y2 - 1));
                    });
                }
                (0, 1) => {
                    // Down
                    // ...
                    // x1.
                    // x2.
                    // ...
                    (-1..=0).for_each(|yd| {
                        outside_cw |= flood_fill(&mut region_cw, (x2 - 1, y2 + yd));
                        outside_ccw |= flood_fill(&mut region_ccw, (x2 + 1, y2 + yd));
                    });
                }
                (-1, 0) => {
                    // Left
                    // .xx.
                    // .21.
                    // ....
                    (0..=1).for_each(|xd| {
                        outside_cw |= flood_fill(&mut region_cw, (x2 + xd, y2 - 1));
                        outside_ccw |= flood_fill(&mut region_ccw, (x2 + xd, y2 + 1));
                    });
                }
                _ => panic!("Invalid direction: ({}, {})", xd, yd),
            }
        });
    assert!(outside_cw ^ outside_ccw);

    let result = if outside_ccw { region_cw } else { region_ccw }.len();

    println!("{result}");
    Ok(())
}
```

The basic idea is that there should be exactly two regions in the image, one 'inside' and one 'outside'. But another way to look at it, one will be clockwise (`cw`) and the other counterclockwise (`ccw`) with respect to the trail you're taking through the pipes (if you `iter` in the opposite direction, these will swap). 

So the algorithm is as follows:

1. For each point along the loop, use the direction you're moving from the previous point and determine two points `clockwise` and two `counterclockwise` along your path; [[wiki:flood fill]]() from each of those points into a calculated region
   1. A flood fill will include a point and (recursively) all neighbors so long as each point is *not*:
      1. On the loop
      2. Out of bounds (this will also mark the region as 'outside')
      3. Already included

After that all is done, we should have exactly one of the two points that crossed the `bounds` of the map, this one is outside and we want the other one. 

There was one gotcha that took me a bit to determine; that is the comment about 'two points `clockwise`'. Without that, it's possible in regions that zigzag a lot to miss a few points that won't otherwise be flood filled. Getting the indexes right for that took a moment as well. 

But once that's all run, we're good to go!

This was an interesting one. No magic (so far as I'm concerned) once you realized that there will always be exactly two regions--'clockwise' and 'counterclockwise'.

## Performance

Still pretty fast, although we're actually passing (*gasp*) a quarter second!

```bash
$ just time 10 1

hyperfine --warmup 3 'just run 10 1'
Benchmark 1: just run 10 1
  Time (mean ± σ):     252.3 ms ±   3.5 ms    [User: 177.2 ms, System: 11.3 ms]
  Range (min … max):   245.3 ms … 257.9 ms    11 runs

$ just time 10 2

hyperfine --warmup 3 'just run 10 2'
Benchmark 1: just run 10 2
  Time (mean ± σ):     261.3 ms ±   3.9 ms    [User: 182.7 ms, System: 12.6 ms]
  Range (min … max):   254.3 ms … 266.3 ms    11 runs
```

I'm okay with this. 