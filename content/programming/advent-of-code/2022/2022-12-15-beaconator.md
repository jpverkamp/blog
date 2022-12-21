---
title: "AoC 2022 Day 15: Beaconator"
date: 2022-12-15 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
## Source: [Beacon Exclusion Zone](https://adventofcode.com/2022/day/15)

## Part 1

> There are a collections of `Sensor`s and `Beacon`s. As input, you are given the `Beacon` closest to each `Sensor` (using {{<wikipedia "Manhattan Distance">}}). If a `Beacon` is not closest to any sensor, it will not appear in this list. Calculate how many points in the given row (`y=2000000`) cannot contain a `Beacon`. 

<!--more-->

Once again with ranges. :D We'll come back to that. 

To start with, we want to parse the input:

```rust
#[derive(Debug)]
struct Map {
    sensors: Vec<(Point, Point)>,
}

impl<I> From<&mut I> for Map
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        let re = Regex::new(
            r"Sensor at x=(-?\d+), y=(-?\d+): closest beacon is at x=(-?\d+), y=(-?\d+)",
        )
        .expect("regex creation failed");

        let mut sensors = Vec::new();

        for line in iter {
            let cap = re.captures(&line).expect("regex doesn't match line");

            sensors.push((
                Point {
                    x: cap[1].parse::<isize>().expect("sensor x must be number"),
                    y: cap[2].parse::<isize>().expect("sensor y must be number"),
                },
                Point {
                    x: cap[3].parse::<isize>().expect("beacon x must be number"),
                    y: cap[4].parse::<isize>().expect("beacon y must be number"),
                },
            ))
        }

        Map { sensors }
    }
}
```

That's easy enough. First time using [`regex`](https://docs.rs/regex/latest/regex/), and it works pretty much exactly as I'd expect. 

Next, what does it actually mean for a point to not be in the `Range` of any `Sensor`? 

Well, I'm going to borrow the diagram from the prompt:

```text
               1    1    2    2
     0    5    0    5    0    5
-2 ..........#.................
-1 .........###................
 0 ....S...#####...............
 1 .......#######........S.....
 2 ......#########S............
 3 .....###########SB..........
 4 ....#############...........
 5 ...###############..........
 6 ..#################.........
 7 .#########S#######S#........
 8 ..#################.........
 9 ...###############..........
10 ....B############...........
11 ..S..###########............
12 ......#########.............
13 .......#######..............
14 ........#####.S.......S.....
15 B........###................
16 ..........#SB...............
17 ................S..........B
18 ....S.......................
19 ............................
20 ............S......S........
21 ............................
22 .......................B....
```

We're specifically looking at the `S` (`Sensor`) in the middle which is related to the `B` (`Beacon`) long the lower left edge of the `#`. Because there is no closer `B` to `S` than that, we know that all the spaces in the diagram with `#` *cannot* be a `Beacon`. Now, take a slice of that:

```text
               1    1    2    2
     0    5    0    5    0    5
 8 ..#################.........
```

That slice is all points that are within the `manhattan_distance(S, B)`. Another way to look at it though is if you go down 1 from `S` to get to this row, all of the points are within `manhattan_distance(S, B) - 1` of the `S`'s X coordinate. Likewise:

```text
               1    1    2    2
     0    5    0    5    0    5
13 .......#######..............
```

We had to go down `6`, so all points are within `manhattan_distance(S, B) - 6`. 

To turn that into code:

```rust
impl Map {
    fn ranges_for(&self, target_row: isize) -> Ranges {
        let mut ranges = Ranges::new();

        for (sensor, beacon) in &self.sensors {
            // Distance = Distance to beacon
            // Offset = How much of that is included in offset distance to target
            // Remaining = How much is in the side to side range
            let distance = sensor.manhattan_distance(&beacon);
            let offset = (sensor.y - target_row).abs();
            let remaining = distance - offset;

            // If we don't have any side to side, the beacon is too far from the target row
            if remaining <= 0 {
                continue;
            }

            // Calculate the range of values in the target row a beacon could not be in
            let mut min_x = sensor.x - remaining;
            let mut max_x = sensor.x + remaining;

            // Special case if the beacon is in the target row
            if beacon.y == target_row && beacon.x == min_x {
                min_x += 1;
            }
            if beacon.y == target_row && beacon.x == max_x {
                max_x -= 1;
            }

            ranges.union(Range::new(min_x, max_x));
        }

        ranges
    }
}
```

We calculate the `distance`, `offset`, and `remaining` as above. The one caveat is that if a `Beacon` is exactly on an edge (and it will be somewhere, just not necessarily in the `target_row` we're looking at), then make sure not to include that. 

All that's left is ... what is `Range`? What is a `Ranges`? And how can you `union` them? 

Well:

```rust
#[derive(Copy, Clone, Debug)]
struct Range {
    min: isize,
    max: isize,
}

impl Range {
    fn new(min: isize, max: isize) -> Self {
        Range { min, max }
    }

    fn union(self, other: Range) -> Option<Range> {
        // One range completely includes the other
        if other.min >= self.min && other.max <= self.max {
            return Some(self);
        }
        if self.min >= other.min && self.max <= other.max {
            return Some(other);
        }

        // One range is partially inside the other
        if other.min >= self.min && other.max <= self.max {
            return Some(Range {
                min: self.min,
                max: other.max,
            });
        }
        if other.max >= self.min && other.max <= self.max {
            return Some(Range {
                min: other.min,
                max: self.max,
            });
        }

        // No overlap
        None
    }

    fn len(&self) -> usize {
        return 1 + (self.max - self.min) as usize;
    }
}
```

A `Range` is a minimum and maximum (inclusive). The `union` of two ranges checks if they are nested or overlapping at all and returns a combined range if so, otherwise returns `None`. 

This lets us make a combined `Ranges`:

```rust
#[derive(Debug)]
struct Ranges {
    data: Vec<Range>,
}

impl Ranges {
    fn new() -> Self {
        Ranges { data: Vec::new() }
    }

    fn union(&mut self, r: Range) {
        self.data.push(r);
        self.collapse();
    }
}
```

That will `push` the new `Range` into the list, but it might overlap any one of the elements. So perhaps the most interesting bit of the algorithm (to me at least), is the one where we want to `collapse` a given `Ranges` into as minimum number of `Range` as we can. 

To do that, try every pair. Any that overlap, `union` them. As long as that keeps working, keep doing it. When we can't, we're done. 

```rust
impl Ranges {
    fn collapse(&mut self) {
        loop {
            let mut to_merge = None;

            'find_merge: for (i, a) in self.data.iter().enumerate() {
                for (j, b) in self.data.iter().enumerate() {
                    if i == j {
                        continue;
                    } else if let Some(c) = a.union(*b) {
                        to_merge = Some((i, j, c));
                        break 'find_merge;
                    }
                }
            }

            if let Some((i, j, c)) = to_merge {
                self.data.remove(i.max(j));
                self.data.remove(i.min(j));
                self.data.push(c);
            } else {
                break;
            }
        }
    }

    fn len(&self) -> usize {
        self.data.iter().map(|r| r.len()).sum::<usize>()
    }
}
```

So we have the code necessary to build and `union` `Ranges`, let's use them!

```rust
fn part1(filename: &Path) -> String {
    let map = Map::from(&mut iter_lines(filename));

    let target_row = if filename
        .file_name()
        .unwrap()
        .to_str()
        .unwrap()
        .contains("test")
    {
        10
    } else {
        2000000
    };

    map.ranges_for(target_row).len().to_string()
}
```

That's it. We do have a special case, since the test data and 'real' data care about different ranges. But other than that, we're really just building up the `Map`, getting the `ranges_for(target_row)` and finding out the `len()` (how many elements). 

Nice. 

## Part 2

> For `0 <= x <= 4000000` and `0 <= y <= 4000000`, there is exactly one point that could be an additional beacon. Find that point and calculate `x * 4000000 + y`.

Interesting. For this one, we don't actually want the unbounded ranges, we want to specifically limit them to the above. To do that, we don't want `union`, but rather `intersection`:

```rust
impl Ranges {
    fn new() -> Self {
        Ranges { data: Vec::new() }
    }

    fn union(&mut self, r: Range) {
        self.data.push(r);
        self.collapse();
    }

    fn intersection(&mut self, r: Range) {
        self.data = self
            .data
            .iter()
            .filter_map(|c| {
                // One range completely includes the other
                if r.min >= c.min && r.max <= c.max {
                    return Some(r);
                }
                if c.min >= r.min && c.max <= r.max {
                    return Some(*c);
                }

                // One range is partially inside the other
                if r.min >= c.min && r.min <= c.max {
                    return Some(Range {
                        min: r.min,
                        max: c.max,
                    });
                }
                if r.max >= c.min && r.max <= c.max {
                    return Some(Range {
                        min: c.min,
                        max: r.max,
                    });
                }

                // No overlap
                None
            })
            .collect();
    }
}
```

This time, we'll go through every point in the current `data` and apply the `intersection` to it. It will either shrink (if there's some overlap) or disappear entirely (if there's none). `filter_map` does that for us and removes the ones that are gone entirely. It's nice having all these functional functions. 

With that in place, we can do part 2:

```rust
fn part2(filename: &Path) -> String {
    let map = Map::from(&mut iter_lines(filename));

    let bound = if filename
        .file_name()
        .unwrap()
        .to_str()
        .unwrap()
        .contains("test")
    {
        20
    } else {
        4000000
    };

    let mut p = None;

    for y in 0..=bound {
        let mut ranges = map.ranges_for(y);
        ranges.intersection(Range::new(0, bound));

        // If we don't have a full range, we have a candidate
        // Candidates have exactly two Range, 0 to x-1 and x+1 to bound
        if ranges.data.len() > 1 {
            let x = ranges
                .data
                .into_iter()
                .find(|r| r.min > 0)
                .expect("must have non-zero x")
                .min
                - 1;

            // Check if the candidate is exactly equal to a beacon
            let new_p = Point { x, y };
            if map.sensors.iter().any(|(_, b)| new_p == *b) {
                continue;
            }

            // If not, we found the solution
            p = Some(new_p);
            break;
        }
    }

    match p {
        Some(Point { x, y }) => (x * 4000000 + y).to_string(),
        None => panic!("no answer found"),
    }
}
```

I did have a gotcha, dealing with the `Beacon`s that were on the border again, thus the `map.sensors.iter().any`. It's not perfect, but I think it's clear enough. And it works!

## Performance

Still quick!

```rust
$ ./target/release/15-beaconator 1 data/15.txt

4724228
took 2.454416ms

$ ./target/release/15-beaconator 2 data/15.txt

13622251246513
took 666.55525ms
```

We do keep getting closer to a second, but still *well* under it. So... onward!