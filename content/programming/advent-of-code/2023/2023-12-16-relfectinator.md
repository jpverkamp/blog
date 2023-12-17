---
title: "AoC 2023 Day 16: Reflectinator"
date: 2023-12-16 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 16: The Floor Will Be Lava](https://adventofcode.com/2023/day/16)

<video controls src="/embeds/2023/aoc23-16.mp4"></video>

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day16) for today (spoilers!)

{{<toc>}}

## Part 1

> You are given a grid of mirrors (`|-\/`) and empty space (`.`). 
>
> Diagonal mirrors just relect the light.  
>
> The horizontal and vertical mirrors are splitters, light hitting them head on (like `>|`) will split to go both directions. Light hitting edge on will just go through it. 
>
> Starting in the top left going East, how many total tiles will a light beam illuminate? 

<!--more-->

Okay, first things first, let's go ahead and extract that [grid](#grid) we've been using. [See below](#grid). 

Other than that, we want some types for `Mirrors` and `Directions`: 

```rust
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub enum Mirror {
    VerticalSplitter,
    HorizontalSplitter,
    ForwardReflector,
    BackwardReflector,
}

#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash)]
pub enum Direction {
    North,
    South,
    East,
    West,
}

impl From<Direction> for Point {
    fn from(d: Direction) -> Self {
        match d {
            Direction::North => Point::NORTH,
            Direction::South => Point::SOUTH,
            Direction::East => Point::EAST,
            Direction::West => Point::WEST,
        }
    }
}
```

With that, we should be able to `illuminate`. Because we can split, I'll keep a [[wiki:queue]]() of current points to check. Each iteration, I'll advance the light by one (possibly splitting). One caveat is to make sure that we don't get into possible loops. As before, keeping a `HashSet` of `visited` `(Point, Direction)` should be sufficient as we can visit the same point with different directions and get different outputs, but the same point and direction will always add the same points to the `illumanation`:

```rust
pub(crate) fn illuminate(mirrors: &Grid<Mirror>, start: (Point, Direction)) -> Grid<bool> {
    use Direction::*;
    use Mirror::*;

    let mut queue = Vec::new();
    queue.push(start);

    let mut visited = fxhash::FxHashSet::default();
    let mut illuminated = Grid::new();

    while let Some((p, d)) = queue.pop() {
        // Ignore points that have gone out of bounds
        if !mirrors.bounds.contains(&p) {
            continue;
        }

        // Don't evaluate the same point + direction more than once
        if visited.contains(&(p, d)) {
            continue;
        }
        visited.insert((p, d));

        illuminated.insert(p, true);

        match (mirrors.get(&p), d) {
            // If you hit a splitter side on (ex >-), you continue in the same direction.
            (Some(VerticalSplitter), North) | (Some(VerticalSplitter), South) => {
                queue.push((p + d.into(), d));
            }
            (Some(HorizontalSplitter), East) | (Some(HorizontalSplitter), West) => {
                queue.push((p + d.into(), d));
            }
            // Otherwise (ex >|), split to the two directions it points
            (Some(VerticalSplitter), _) => {
                queue.push((p + North.into(), North));
                queue.push((p + South.into(), South));
            }
            (Some(HorizontalSplitter), _) => {
                queue.push((p + East.into(), East));
                queue.push((p + West.into(), West));
            }
            // Diagonal reflectors just change, so >\ goes South, >/ goes North etc
            (Some(ForwardReflector), North) => queue.push((p + East.into(), East)),
            (Some(ForwardReflector), East) => queue.push((p + North.into(), North)),
            (Some(ForwardReflector), South) => queue.push((p + West.into(), West)),
            (Some(ForwardReflector), West) => queue.push((p + South.into(), South)),

            (Some(BackwardReflector), North) => queue.push((p + West.into(), West)),
            (Some(BackwardReflector), East) => queue.push((p + South.into(), South)),
            (Some(BackwardReflector), South) => queue.push((p + East.into(), East)),
            (Some(BackwardReflector), West) => queue.push((p + North.into(), North)),
            // If there's nothing there, keep going
            (None, _) => queue.push((p + d.into(), d)),
        }
    }

    illuminated
}
```

Bit of a big `match` there, but I think that it's pretty straight forward? One thing that I like is that because of how `match` statements work in Rust, if I miss any cases, it will yell at me!

Okay, let's plug it in:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();

    let input = io::read_to_string(stdin.lock())?;
    let mirrors = Grid::read(&input, |c| match c {
        '|' => Some(Mirror::VerticalSplitter),
        '-' => Some(Mirror::HorizontalSplitter),
        '/' => Some(Mirror::ForwardReflector),
        '\\' => Some(Mirror::BackwardReflector),
        _ => None,
    });

    let illuminated = illuminate(&mirrors, (Point::new(0, 0), Direction::East));
    let result = illuminated.iter().count();

    println!("{result}");
    Ok(())
}
```

Sweet. 

I like the new [grid](#grid) interface. :smile:


## Part 2

> Assuming the light could start on any of the 4 edges, what is the maximum illumination? 

Well, we already have the function. Let's just try them all!

```rust
mod part1;
use part1::illuminate;

fn main() -> Result<()> {
    let stdin = io::stdin();
    use Direction::*;

    let input = io::read_to_string(stdin.lock())?;
    let mirrors = Grid::read(&input, |c| match c {
        '|' => Some(Mirror::VerticalSplitter),
        '-' => Some(Mirror::HorizontalSplitter),
        '/' => Some(Mirror::ForwardReflector),
        '\\' => Some(Mirror::BackwardReflector),
        _ => None,
    });

    let mut starts = Vec::new();
    for x in mirrors.bounds.min_x..=mirrors.bounds.max_x {
        starts.push((Point::new(x, mirrors.bounds.min_y), South));
        starts.push((Point::new(x, mirrors.bounds.max_y), North));
    }
    for y in mirrors.bounds.min_y..=mirrors.bounds.max_y {
        starts.push((Point::new(mirrors.bounds.min_x, y), East));
        starts.push((Point::new(mirrors.bounds.max_x, y), West));
    }

    let result = starts
        .iter()
        .map(|start| illuminate(&mirrors, *start).iter().count())
        .max()
        .unwrap();

    println!("{result}");
    Ok(())
}
```

Pulling `illuminate` from the other `bin` is a bit weird... but it works fine! Just need to generate all of the `starts` and try them. 

## Performance

Plenty quick:

```bash
$ just time 16 1

hyperfine --warmup 3 'just run 16 1'
Benchmark 1: just run 16 1
  Time (mean ± σ):      83.3 ms ±   3.3 ms    [User: 32.3 ms, System: 12.6 ms]
  Range (min … max):    78.8 ms …  92.2 ms    32 runs

$ just time 16 2

hyperfine --warmup 3 'just run 16 2'
Benchmark 1: just run 16 2
  Time (mean ± σ):     206.9 ms ±   3.7 ms    [User: 129.8 ms, System: 15.5 ms]
  Range (min … max):   200.5 ms … 214.2 ms    14 runs
```

It's mostly disk I/O. You can tell that especially in part 2. Despite doing more than 400 as much work, it's only ~2.5x slower--because we only have to load the data once. 

## Grid

As a side note, the implementation of Grid!

### Implementation

The goal of `Grid` was to create a [[wiki:sparse grid]]() of points (where most are empty). 

So rather than allocating memory for each possible point, we only keep a `HashMap` from [`Point`](#point) to some generic type `T`. 

What I think is particularly cool is that (like most of Rust), you generally don't have to specify the generic type `T`. If you provide a conversion function to `read` (as we did in [loading the mirrors](#part-1)) or just `insert` values yourself (as we do in [illuminate](#part-1)) it will just figure it out. That's pretty cool. :smile:

```rust
#[derive(Debug)]
pub struct Grid<T> {
    pub bounds: Bounds,
    data: FxHashMap<Point, T>,
}

impl<T: Default> Default for Grid<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T> Grid<T> {
    pub fn new() -> Self {
        Self {
            bounds: Bounds::default(),
            data: FxHashMap::default(),
        }
    }

    pub fn read(s: &str, from_c: impl Fn(char) -> Option<T>) -> Self {
        let mut grid = Self::new();
        for (y, line) in s.lines().enumerate() {
            for (x, c) in line.chars().enumerate() {
                if let Some(c) = from_c(c) {
                    grid.insert(Point { x: x as isize, y: y as isize }, c);
                }
            }
        }
        grid
    }

    pub fn get(&self, point: &Point) -> Option<&T> {
        self.data.get(point)
    }

    pub fn get_mut(&mut self, point: &Point) -> Option<&mut T> {
        self.data.get_mut(point)
    }

    pub fn insert(&mut self, point: Point, value: T) {
        self.bounds.include(point);
        self.data.insert(point, value);
    }

    pub fn remove(&mut self, point: &Point) -> Option<T> {
        self.data.remove(point)
    }

    pub fn iter(&self) -> impl Iterator<Item = (&Point, &T)> {
        self.data.iter()
    }

    pub fn iter_mut(&mut self) -> impl Iterator<Item = (&Point, &mut T)> {
        self.data.iter_mut()
    }

    pub fn iter_points(&self) -> impl Iterator<Item = &Point> {
        self.data.keys()
    }

    pub fn iter_values(&self) -> impl Iterator<Item = &T> {
        self.data.values()
    }

    pub fn iter_values_mut(&mut self) -> impl Iterator<Item = &mut T> {
        self.data.values_mut()
    }
}
```

In addition, to make this work, we also have extracted [`Point`](#point) and [`Bounds`](#bounds) into their own packages as well. I feel like we might want these all in one... but for now it works. 

### Point

As before, a point is `isize`. This allows us to add/subtract points without worrying about underflow!

```rust
#[derive(Debug, Copy, Clone, Eq, PartialEq, Hash, Ord, PartialOrd)]
pub struct Point {
    pub x: isize,
    pub y: isize,
}

impl Point {
    pub const NORTH: Point = Point { x: 0, y: -1 };
    pub const SOUTH: Point = Point { x: 0, y: 1 };
    pub const EAST: Point = Point { x: 1, y: 0 };
    pub const WEST: Point = Point { x: -1, y: 0 };

    pub fn new(x: isize, y: isize) -> Self {
        Self { x, y }
    }

    pub fn manhattan_distance(&self, other: &Point) -> isize {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }
}

impl std::ops::Add<Point> for Point {
    type Output = Point;

    fn add(self, rhs: Point) -> Self::Output {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
        }
    }
}

impl std::ops::Sub<Point> for Point {
    type Output = Point;

    fn sub(self, rhs: Point) -> Self::Output {
        Point {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
        }
    }
}

impl std::fmt::Display for Point {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
```

### Bounds

And finally `Bounds`. This represents a bounding box. The neat part to me is that you can extend it with `include`. I feel like that needs a better name. Anyways:

```rust
use point::Point;

#[derive(Debug, Copy, Clone, Eq, PartialEq, Default, Hash)]
pub struct Bounds {
    pub min_x: isize,
    pub max_x: isize,
    pub min_y: isize,
    pub max_y: isize,
}

impl Bounds {
    pub fn contains(&self, point: &Point) -> bool {
        point.x >= self.min_x
            && point.x <= self.max_x
            && point.y >= self.min_y
            && point.y <= self.max_y
    }

    pub fn include(&mut self, p: Point) {
        self.min_x = self.min_x.min(p.x);
        self.max_x = self.max_x.max(p.x);
        self.min_y = self.min_y.min(p.y);
        self.max_y = self.max_y.max(p.y);
    }
}
```

## Edit 1, Adding to_string and to_image for Grid

It's nice to be able to debug and we can basically reverse the `from_c` function:

```rust
impl Grid<T> {
        pub fn to_string(&self, empty_c: char, to_c: impl Fn(&T) -> char) -> String {
        let mut s = String::new();

        for y in self.bounds.min_y..=self.bounds.max_y {
            for x in self.bounds.min_x..=self.bounds.max_x {
                let p = Point { x, y };
                if let Some(c) = self.get(&p).map(&to_c) {
                    s.push(c);
                } else {
                    s.push(empty_c);
                }
            }
            s.push('\n');
        }

        s
    }

    pub fn to_image(
        &self,
        empty_c: image::Rgba<u8>,
        to_c: impl Fn(&T) -> image::Rgba<u8>,
    ) -> image::RgbaImage {
        let width = self.bounds.max_x - self.bounds.min_x + 1;
        let height = self.bounds.max_y - self.bounds.min_y + 1;

        let mut image = image::RgbaImage::new(width as u32, height as u32);

        for y in self.bounds.min_y..=self.bounds.max_y {
            for x in self.bounds.min_x..=self.bounds.max_x {
                let p = Point { x, y };
                if let Some(c) = self.get(&p).map(&to_c) {
                    image.put_pixel(
                        (x - self.bounds.min_x) as u32,
                        (y - self.bounds.min_y) as u32,
                        c,
                    );
                } else {
                    image.put_pixel(
                        (x - self.bounds.min_x) as u32,
                        (y - self.bounds.min_y) as u32,
                        empty_c,
                    );
                }
            }
        }

        image
    }
}
```

With that, we can make a nice `part2-render.rs`:

```rust
let background = mirrors.to_image(image::Rgba([0, 0, 0, 0]), |_| {
    image::Rgba([255, 255, 255, 255])
});
let barely_black = image::RgbaImage::from_pixel(
    background.width(),
    background.height(),
    image::Rgba([0, 0, 0, 8]),
);
let mut foreground = image::RgbaImage::new(background.width(), background.height());

let mut frame = 0;
while let Some(points) = queue.pop() {
    if frame > RENDER_FRAMES {
        break;
    }

    // Render the current frame
    {
        frame += 1;
        let filename = format!("frames/{:04}.png", frame);
        println!("Rendering {}", filename);

        create_dir_all("frames").ok();

        let mut frame = image::RgbaImage::new(background.width(), background.height());

        // Darken the previous foreground frames slightly
        image::imageops::overlay(&mut foreground, &barely_black, 0, 0);

        for (p, _) in &points {
            if mirrors.bounds.contains(&p) {
                foreground.put_pixel(p.x as u32, p.y as u32, image::Rgba([255, 0, 0, 255]));
            }
        }

        image::imageops::overlay(&mut frame, &foreground, 0, 0);
        image::imageops::overlay(&mut frame, &background, 0, 0);
        frame.save(filename).unwrap();
    }

    // ...
}
```

I did tweak it to 1) not check `visited` points, so that we get full effect and 2) keep an ever growing list of the current points, rather than the more efficient queue. I think the results are pretty cool!

<video controls src="/embeds/2023/aoc23-16.mp4"></video>
