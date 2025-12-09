---
title: "AoC 2025 Day 9: Polygoninator"
date: 2025-12-09 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2025
programming/topics: []
---
## Source: [Day 9: Movie Theater](https://adventofcode.com/2025/day/9)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2025/src/day9.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a list of points (2D), find the pair of points which form the largest rectangle. 

<!--more-->

```rust
#[aoc::register]
fn part1(input: &str) -> impl Into<String> {
    let points = input.lines().map(Point2D::from).collect::<Vec<_>>();

    let mut max_area = 0;

    for i in 0..points.len() {
        for j in i + 1..points.len() {
            let xd = (points[i].x - points[j].x).abs() + 1;
            let yd = (points[i].y - points[j].y).abs() + 1;
            let area = xd * yd;

            if area > max_area {
                max_area = area;
            }
        }
    }

    max_area.to_string()
}
```

I expect you could estimate a bit more by *looking* at the points, but honestly, this works fine. 

```bash
$ just run-and-bench 9 part1

4749929916

part1: 117.402µs ± 5.432µs [min: 108.583µs, max: 146.583µs, median: 117.791µs]
```

## Part 2

> The points define a polygon. Find the largest rectangle made by two points that lies entirely within the polygon. 

Well isn't that fun. 

At the very least it's worth making a few helper classes:

### line2d.rs

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct Line2D {
    start: Point2D,
    end: Point2D,
}

impl Line2D {
    pub fn new(start: Point2D, end: Point2D) -> Self {
        Line2D { start, end }
    }

    pub fn intersects(&self, other: &Line2D) -> bool {
        let d1 = (self.end.x - self.start.x) * (other.start.y - self.start.y)
            - (self.end.y - self.start.y) * (other.start.x - self.start.x);
        let d2 = (self.end.x - self.start.x) * (other.end.y - self.start.y)
            - (self.end.y - self.start.y) * (other.end.x - self.start.x);
        let d3 = (other.end.x - other.start.x) * (self.start.y - other.start.y)
            - (other.end.y - other.start.y) * (self.start.x - other.start.x);
        let d4 = (other.end.x - other.start.x) * (self.end.y - other.start.y)
            - (other.end.y - other.start.y) * (self.end.x - other.start.x);

        if ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))
        {
            return true;
        }

        false
    }
}
```

Why, yes. I did write test cases for that. It's bonkers looking. 

### polygon.rs

```rust
#[derive(Debug, Clone)]
pub struct Polygon {
    vertices: Vec<Point2D>,
}

impl Polygon {
    pub fn new(vertices: Vec<Point2D>) -> Self {
        Polygon { vertices }
    }

    // Check if a point is inside the polygon using the ray-casting algorithm
    // Source: https://www.xjavascript.com/blog/check-if-polygon-is-inside-a-polygon/
    pub fn contains(&self, point: &Point2D) -> bool {
        let mut inside = false;
        let n = self.vertices.len();

        for i in 0..n {
            let j = (i + n - 1) % n;

            let pi = &self.vertices[i];
            let pj = &self.vertices[j];

            // TODO: On edge check

            if (pi.y > point.y) != (pj.y > point.y) {
                let x_intersect = (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y) + pi.x;
                if point.x < x_intersect {
                    inside = !inside;
                }
            }
        }

        inside
    }
}
```

I ended up working around the edge check in this case, so I'll implement that later if we need it. 

### Back to the problem

```rust
#[aoc::register]
fn part2(input: &str) -> impl Into<String> {
    let points = input.lines().map(Point2D::from).collect::<Vec<_>>();
    let polygon = Polygon::new(points.clone());

    let mut max_area = 0;

    for i in 0..points.len() {
        for j in i + 1..points.len() {
            // All 4 vertices must be within the polygon
            // Because the polygons are on a grid of points, this means we can ignore the edge checks
            // This will skip rectangles with width/height = 1, but those won't be max area (we assume)
            let vertices = [
                Point2D::new(
                    points[i].x.min(points[j].x) + 1,
                    points[i].y.min(points[j].y) + 1,
                ),
                Point2D::new(
                    points[i].x.min(points[j].x) + 1,
                    points[i].y.max(points[j].y) - 1,
                ),
                Point2D::new(
                    points[i].x.max(points[j].x) - 1,
                    points[i].y.min(points[j].y) + 1,
                ),
                Point2D::new(
                    points[i].x.max(points[j].x) - 1,
                    points[i].y.max(points[j].y) - 1,
                ),
            ];
            if !vertices.iter().all(|v| polygon.contains(v)) {
                continue;
            }

            // No edge of the rectangle can intersect with any edge of the polygon
            let rectangle_edges = vec![
                Line2D::new(vertices[0], vertices[1]),
                Line2D::new(vertices[1], vertices[3]),
                Line2D::new(vertices[3], vertices[2]),
                Line2D::new(vertices[2], vertices[0]),
            ];

            let mut intersects = false;
            'outer: for rect_edge in &rectangle_edges {
                for i in 0..points.len() {
                    let poly_edge = Line2D::new(points[i], points[(i + 1) % points.len()]);
                    if rect_edge.intersects(&poly_edge) {
                        intersects = true;
                        break 'outer;
                    }
                }
            }
            if intersects {
                continue;
            }

            let xd = (points[i].x - points[j].x).abs() + 1;
            let yd = (points[i].y - points[j].y).abs() + 1;
            let area = xd * yd;

            if area > max_area {
                max_area = area;
            }
        }
    }

    max_area.to_string()
}
```

That's a bit longer, isn't it. 

One point worth repeating is the comment:

> All 4 vertices must be within the polygon
>
> Because the polygons are on a grid of points, this means we can ignore the edge checks
>
> This will skip rectangles with width/height = 1, but those won't be max area (we assume)

Basically, the problem here is that the points we have are entire cells, so we're going to be off by one on one side or the other. And what's worse, we didn't do that edge checking I was talking about. This lets us skip that: If a rectangle one smaller in each dimension is in the polygon, for this puzzle, that is good enough.

And it works!

```bash
$ just run-and-bench 9 part2

1572047142

part2: 117.595123ms ± 2.790635ms [min: 115.400375ms, max: 139.578917ms, median: 116.955541ms]
```

*Quite* a bit slower though.

One thing we can do is to move the `area < max_area` check above the polygon check. Once we've found the first valid rectangle, this will mean we can throw out the relatively expensive polygon contains checks. 

```bash
$ just run-and-bench 9 part2_area_first

1572047142

part2_area_first: 75.403609ms ± 828.472µs [min: 74.197709ms, max: 82.072625ms, median: 75.324333ms]
```

Well. It is faster!

If I have time, I'll come back and optimize that one. It really shouldn't be that slow. 

## Visualization

So. What does this thing actually look like?

Well, to explain that, I added `render_svg!` and `render_svg_frame!` macros, the latter of which rasterizes each to a `PNG` before making a video. It takes a minute. 

So what does our polygon look like?

<img width="100%" src="/embeds/2025/aoc/aoc2025_day9_polygon_render.svg" />

> That's no moon. 

Well. That explains a few things. :smile: 

It's such a weird looking shape to do as a polygon...

If we animate our search:

<video width="100%" controls src="/embeds/2025/aoc/aoc2025_day9_part2_svg.mp4"></video>

Red rectangles aren't in bounds. Yellow are, but are smaller than our current best. Light green is our current best and dark green marks finding new bests. 

## Benchmarks

```rust
$ just bench 9

part1: 113.22µs ± 5.711µs [min: 103.625µs, max: 145.292µs, median: 112.667µs]
part2: 117.772829ms ± 5.835355ms [min: 114.875834ms, max: 163.092666ms, median: 116.408125ms]
part2_area_first: 75.460115ms ± 4.87159ms [min: 73.968291ms, max: 122.868208ms, median: 74.794209ms]
```

| Day | Part | Solution           | Benchmark                 |
| --- | ---- | ------------------ | ------------------------- |
| 9   | 1    | `part1`            | 113.22µs ± 5.711µs        |
| 9   | 2    | `part2`            | 117.772829ms ± 5.835355ms |
| 9   | 2    | `part2_area_first` | 75.460115ms ± 4.87159ms   |