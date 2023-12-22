---
title: "AoC 2023 Day 21: Step Step Stepinator"
date: 2023-12-21 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 21: Step Counter](https://adventofcode.com/2023/day/21)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day21) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a(n infinite) grid of walls `#`, count how many points can be reached by exactly 64 steps from a starting point.  

<!--more-->

### Parsing

I'm not going to use any more types, but I am going to wrap `Grid` to just return the points and starting location:

```rust
pub fn read(input: &str) -> (FxHashSet<Point>, Point) {
    let walls = Grid::read(input, |c| if c == '#' { Some(true) } else { None });
    let walls = walls.iter().map(|(p, _)| *p).collect::<FxHashSet<_>>();

    let start = Grid::read(input, |c| if c == 'S' { Some(true) } else { None });
    let start = *start.iter().next().unwrap().0;

    (walls, start)
}
```

### Solution

Okay, let's do it:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (walls, start) = parse::read(&input);

    let mut active = FxHashSet::default();
    active.insert(start);

    for _i in 1..=STEPS {
        let mut next_active = FxHashSet::default();

        for pos in active {
            for neighbor in pos.neighbors() {
                if !walls.contains(&neighbor) {
                    next_active.insert(neighbor);
                }
            }
        }

        active = next_active;
    }

    let result = active.len();

    println!("{result}");
    Ok(())
}
```


### Re-calculating Bounds

One problem that doesn't come up in the solution, but did with debug printing is that we lose the `Bounds` information that a `Grid` stores. Let's make it possible to recalculate that (hacky, I know) from any `Iterator<Item = Point>`:

```rust
impl<'a, I> From<I> for Bounds
where
    I: IntoIterator<Item = &'a Point>,
{
    fn from(value: I) -> Self {
        let mut bounds = Bounds::default();
        for p in value {
            bounds.include(*p);
        }
        bounds
    }
}
```

So we can get it back with `let wall_bounds = Bounds::from(walls.iter())`. Pretty cool that. 

## Part 2

> Repeat the input grid infinitely. How many points can be visited in exactly 26501365 steps. 

... right. 

### Brute Force

Well, we can try it of course:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (walls, start) = parse::read(&input);
    let wall_bounds = Bounds::from(walls.iter());

    // Note: Assuming min bounds are 0
    let width = wall_bounds.max_x + 2;
    let height = wall_bounds.max_y + 2;

    // A modular wall function
    let wall_mod_contains = |&p: &Point| {
        let mut p = Point::new(p.x % width, p.y % height);

        if p.x < 0 {
            p.x += width;
        }
        if p.y < 0 {
            p.y += height;
        }

        walls.contains(&p)
    };

    let mut active = FxHashSet::default();
    active.insert(start);

    for _i in 1..=STEPS {
        let mut next_active = FxHashSet::default();

        for pos in active {
            for neighbor in pos.neighbors() {
                if !wall_mod_contains(&neighbor) {
                    next_active.insert(neighbor);
                }
            }
        }

        active = next_active;
    }

    let result = active.len();

    println!("{result}");
    Ok(())
}
```

With that modular wall function, it actually even works pretty well. But `active` gets really big really quick, which makes everything very slow. 

So... 

### Solution

One thing to note is that despite all of the walls in the input, if you look carefully, you'll note that the entire horizontal line in the very center of the image is empty... (the same up and down). 

So in exactly `cell_width / 2` steps, we'll start the cells to the left and right. Exactly `cell_width` after that, we'll start the ones after that. Given the 131 wide input, we have a cycle starting at `step=65` with `cycle=131`. 

What's more, because of these nice empty rows, we also know that the total area is going to grow [[wiki:quadratically]](), out in 2D square instead of on a line. 

So what we want will be to calculate the points at `x=0, 1, 2, ...` where `steps=65, 196, 327`. With three of those, we can do some [crazy math](https://stackoverflow.com/questions/19175037/determine-a-b-c-of-quadratic-equation-using-data-points) to extrapolate to any specific point... so long as it's of the form `131x+65`...

{{<latex>}}
26501365 = 202300 * 131 + 65
{{</latex>}}

Huh. Look at that. :smile:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;

    let (walls, start) = parse::read(&input);
    let wall_bounds = Bounds::from(walls.iter());

    // Note: Assuming min bounds are 0
    // The original cell takes cell_width/2 steps to reach the edge
    // And then each cell takes cell_width steps to fill across
    let cell_width = wall_bounds.max_x + 2;
    let cell_height = wall_bounds.max_y + 2;
    let half_width = cell_width / 2;

    // Find the number of cycles it would take to get to the target
    // If this doesn't evenly divide, messy things happen
    let target = ((STEPS as isize) - half_width) / cell_width;

    // A modular wall function
    let wall_mod_contains = |&p: &Point| {
        let mut p = Point::new(p.x % cell_width, p.y % cell_height);

        if p.x < 0 {
            p.x += cell_width;
        }
        if p.y < 0 {
            p.y += cell_height;
        }

        walls.contains(&p)
    };

    // The set of active points
    let mut active = FxHashSet::default();
    active.insert(start);

    // We're not going to have to actually need to iterate this far
    let mut points = Vec::new();
    for step in 1..=STEPS {
        let mut next_active = FxHashSet::default();

        for pos in active {
            for neighbor in pos.neighbors() {
                if !wall_mod_contains(&neighbor) {
                    next_active.insert(neighbor);
                }
            }
        }

        active = next_active;

        if ((step as isize) - half_width) % cell_width == 0 {
            let i = ((step as isize) - half_width) / cell_width;
            let p = Point::new(i, active.len() as isize);
            points.push(p);

            println!("{step} {p}");

            if points.len() == 3 {
                break;
            }
        }
    }

    // Solve the quadratic equation
    // https://stackoverflow.com/questions/19175037/determine-a-b-c-of-quadratic-equation-using-data-points
    let a = points[0].y / ((points[0].x - points[1].x) * (points[0].x - points[2].x))
        + points[1].y / ((points[1].x - points[0].x) * (points[1].x - points[2].x))
        + points[2].y / ((points[2].x - points[0].x) * (points[2].x - points[1].x));

    let b = -points[0].y * (points[1].x + points[2].x)
        / ((points[0].x - points[1].x) * (points[0].x - points[2].x))
        - points[1].y * (points[0].x + points[2].x)
            / ((points[1].x - points[0].x) * (points[1].x - points[2].x))
        - points[2].y * (points[0].x + points[1].x)
            / ((points[2].x - points[0].x) * (points[2].x - points[1].x));

    let c = points[0].y * points[1].x * points[2].x
        / ((points[0].x - points[1].x) * (points[0].x - points[2].x))
        + points[1].y * points[0].x * points[2].x
            / ((points[1].x - points[0].x) * (points[1].x - points[2].x))
        + points[2].y * points[0].x * points[1].x
            / ((points[2].x - points[0].x) * (points[2].x - points[1].x));

    let target = target as i128;
    let result = (a as i128) * target * target + (b as i128) * target + (c as i128);

    println!("{result}");
    Ok(())
}
```

Yeah... it doesn't work at all if you don't have a perfect multiple. But it works well enough for all that. 

### Another option

One other option that I was going to look into was to basically implement [[wiki:hashlife]](). It takes a [[wiki:cellular automata]]() on an infinite grid (sound familiar) and hashes it as a [[wiki:recursive]]() [[wiki:quadtree]](). I'm pretty sure this would work for *exactly* what we're dealing with. But... I don't have the time right now. 

Perhaps another day. 

So it goes. 

## Performance

```bash
$ just time 21 1

hyperfine --warmup 3 'just run 21 1'
Benchmark 1: just run 21 1
  Time (mean ± σ):     111.7 ms ±   5.8 ms    [User: 44.0 ms, System: 19.9 ms]
  Range (min … max):    99.6 ms … 120.9 ms    28 runs

$ just time 21 2

hyperfine --warmup 3 'just run 21 2'
Benchmark 1: just run 21 2
  Time (mean ± σ):     755.3 ms ±  13.3 ms    [User: 636.4 ms, System: 38.2 ms]
  Range (min … max):   737.5 ms … 787.2 ms    10 runs
```

Even with that massive skip, it's still almost a second. Goodness we're getting slow there. :smile: But it's still under, so onward!