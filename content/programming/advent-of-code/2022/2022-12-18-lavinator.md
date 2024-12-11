---
title: "AoC 2022 Day 18: Lavinator"
date: 2022-12-18 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Algorithms
- Data Structures
- Graphs
---
## Source: [Boiling Boulders](https://adventofcode.com/2022/day/18)

## Part 1

> Given a list of 1x1x1 cubes, determine the total surface area of the cubes. 

<!--more-->

Sweet. Let's make a `Point3D` class to match the earlier `Point`:

```rust
/* ----- A 3D version of the point ----- */
#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Point3D {
    pub x: isize,
    pub y: isize,
    pub z: isize,
}

impl Add for Point3D {
    type Output = Point3D;

    fn add(self, rhs: Self) -> Self::Output {
        Point3D::new(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)
    }
}

impl Sub for Point3D {
    type Output = Point3D;

    fn sub(self, rhs: Self) -> Self::Output {
        Point3D::new(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)
    }
}

impl Point3D {
    pub const UNITS: [Point3D; 6] = [
        Point3D { x: -1, y: 0, z: 0 },
        Point3D { x: 1, y: 0, z: 0 },
        Point3D { x: 0, y: -1, z: 0 },
        Point3D { x: 0, y: 1, z: 0 },
        Point3D { x: 0, y: 0, z: -1 },
        Point3D { x: 0, y: 0, z: 1 },
    ];

    pub fn new(x: isize, y: isize, z: isize) -> Self {
        Point3D { x, y, z }
    }

    pub fn adjacent_to(self, other: Point3D) -> bool {
        let delta = self - other;

        delta.x == 0 && delta.y == 0 && delta.z.abs() == 1
            || delta.x == 0 && delta.y.abs() == 1 && delta.z == 0
            || delta.x.abs() == 1 && delta.y == 0 && delta.z == 0
    }
}
```

`adjacent_to` is something we'll need just for this problem, but let's go ahead and write it. `Point3D::UNITS` is the six unit vectors. We'll use that to get the six cubes that might touch a given cube

Next, a collection struct of `Point3D`: `Point3DCloud`:

```rust
#[derive(Debug)]
struct Point3DCloud {
    points: HashSet<Point3D>,
}

impl Point3DCloud {
    fn contains(&self, p: Point3D) -> bool {
        self.points.contains(&p)
    }
}

impl<I> From<&mut I> for Point3DCloud
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        Point3DCloud {
            points: iter
                .map(|line| {
                    let (x, y, z) = line
                        .split(',')
                        .map(|v| v.parse::<isize>().expect("must be numbers"))
                        .collect_tuple()
                        .expect("must have three elements");
                    Point3D::new(x, y, z)
                })
                .collect::<HashSet<_>>(),
        }
    }
}
```

Easy enough, once again `HashSet` to contain a bunch of points with arbitrary bounds that is quick to check `contains`. 

That should be enough:

```rust
fn part1(filename: &Path) -> String {
    let cloud = Point3DCloud::from(&mut iter_lines(filename));

    cloud
        .points
        .iter()
        .map(|p| {
            Point3D::UNITS
                .iter()
                .map(|s| !cloud.contains(*p + *s))
                .filter(|v| *v)
                .count()
        })
        .sum::<usize>()
        .to_string()
}
```

Elegant. Great the point cloud, than for each point, for each side of that point, if the cube to the side of the point is not itself in the cloud, the side counts for surface area. 

I'm not sure that was any easier to read than the code honestly. :smile:

## Part 2

> The collection of points is hollow. Calculate only the external surface area. 

Well that's neat. 

To do this, the first thing I want to do is to create a second set of points: `external`. For this, I want all points that are 'outside' of the `cloud`. To generate this list, I need `Point3DCloud::bounds`, a bound outside of the `bounds`, and to [[wiki:flood fill]]() from that point to fill the bounds. 

Once I've done that, any points in the flood fill are `external`, so we can use very nearly the same code as above. If for each cube, for each side, if the next cube on that side is `external`, this is an external surface. 

```rust
impl Point3DCloud {
    fn bounds(&self) -> (Point3D, Point3D) {
        let mut min_bound = Point3D::new(isize::MAX, isize::MAX, isize::MAX);
        let mut max_bound = Point3D::new(isize::MIN, isize::MIN, isize::MIN);

        self.points.iter().for_each(|p| {
            min_bound.x = min_bound.x.min(p.x);
            min_bound.y = min_bound.y.min(p.y);
            min_bound.z = min_bound.z.min(p.z);

            max_bound.x = max_bound.x.max(p.x);
            max_bound.y = max_bound.y.max(p.y);
            max_bound.z = max_bound.z.max(p.z);
        });

        (min_bound, max_bound)
    }
}

fn part2(filename: &Path) -> String {
    let cloud = Point3DCloud::from(&mut iter_lines(filename));
    let (mut min_bound, mut max_bound) = cloud.bounds();
    min_bound = min_bound - Point3D::new(1, 1, 1);
    max_bound = max_bound + Point3D::new(1, 1, 1);

    // Calculate all cubes within bounds (expand by one) that are 'external'
    // Do this by starting in one corner and flood filling from the bounds inwards
    let mut external = HashSet::new();

    let mut q = VecDeque::new();
    q.push_back(min_bound);

    while !q.is_empty() {
        let p = q.pop_front().unwrap();

        // Ignore points we've already explored
        if external.contains(&p) {
            continue;
        }

        // Points in the cloud are not external
        if cloud.contains(p) {
            continue;
        }

        // Points out of bounds are ignored
        if p.x < min_bound.x
            || p.y < min_bound.y
            || p.z < min_bound.z
            || p.x > max_bound.x
            || p.y > max_bound.y
            || p.z > max_bound.z
        {
            continue;
        }

        // Otherwise, mark as external
        external.insert(p);

        // Check all neighbors
        Point3D::UNITS.iter().for_each(|s| q.push_back(p + *s));
    }

    // Any side adjacent to an external cube is external
    cloud
        .points
        .iter()
        .map(|p| {
            Point3D::UNITS
                .iter()
                .map(|s| external.contains(&(*p + *s)))
                .filter(|v| *v)
                .count()
        })
        .sum::<usize>()
        .to_string()
}
```

The flood fill should be straight forward enough:

* Create a queue of points, seed it with one point you're flood filling from
* While the queue isn't empty, take a point:
  * If that point is outside of the bounds, skip it
  * If that point has already been scanned (it's in `external`) skip it
  * If that point is in the `cloud`, it's not part of the fill, skip it
  * Otherwise, add the point to the flood fill and then for each neighbor:
    * Add the neighbor to the queue; note: most of these will be skipped and that's fine, just so long as we don't oscillate back and forth


And that's it. Two parts in much less time than [[AoC 2022 Day 16: Pressurinator|Pressurinator]](). 

## Performance

```bash
$ ./target/release/18-lavinator 1 data/18.txt

4548
took 5.440583ms

$ ./target/release/18-lavinator 2 data/18.txt

2588
took 6.8895ms
```

The runtime is completely bounded by the number of points (for part 1) and the bounds of the points (part 2). Since the shape is very roughly a sphere, it's pretty quick. I really should visualize this one, it'd be neat. Perhaps I'll come back to it. 

Onward!