---
title: "AoC 2023 Day 18: Flood Fillinator"
date: 2023-12-18 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2023
---
## Source: [Day 18: Lavaduct Lagoon](https://adventofcode.com/2023/day/18)

[Full solution](https://github.com/jpverkamp/advent-of-code/tree/master/2023/solutions/day18) for today (spoilers!)

{{<toc>}}

## Part 1

> Given a sequence of direction + distance that draws a polygon, calculate the area. 

<!--more-->

### Types and Parsing

It's been a bit. Let's write a proper `nom` parser again. 

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Up,
    Down,
    Left,
    Right,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HexColor {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

impl HexColor {
    pub fn to_hex(&self) -> String {
        format!("#{:02x}{:02x}{:02x}", self.red, self.green, self.blue)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Command {
    pub direction: Direction,
    pub steps: u64,
    pub color: HexColor,
}

impl From<Direction> for Point {
    fn from(d: Direction) -> Self {
        match d {
            Direction::Up => Point::new(0, -1),
            Direction::Down => Point::new(0, 1),
            Direction::Left => Point::new(-1, 0),
            Direction::Right => Point::new(1, 0),
        }
    }
}
```

Pretty standard. I'm going ahead to parse the provided color for each point (although it [turns out](#part-2) ... I didn't want to do that. Oh well.)

```rust
// Parse #rrggbb into Color { r, g, b }
fn hexcolor(input: &str) -> IResult<&str, HexColor> {
    preceded(
        char('#'),
        map_res(hex_digit1, |s: &str| {
            if s.len() == 6 {
                Ok(HexColor {
                    red: u8::from_str_radix(&s[0..2], 16).unwrap(),
                    green: u8::from_str_radix(&s[2..4], 16).unwrap(),
                    blue: u8::from_str_radix(&s[4..6], 16).unwrap(),
                })
            } else {
                Err("invalid hex color")
            }
        }),
    )(input)
}

fn direction(input: &str) -> IResult<&str, Direction> {
    alt((
        map(tag("U"), |_| Direction::Up),
        map(tag("D"), |_| Direction::Down),
        map(tag("L"), |_| Direction::Left),
        map(tag("R"), |_| Direction::Right),
    ))(input)
}

// Parse a line into a command
// Lines look like R 5 (#rrggbb)
fn command(input: &str) -> IResult<&str, Command> {
    let (input, (direction, steps, color)) = tuple((
        direction,
        preceded(multispace1, complete::u64),
        preceded(multispace1, delimited(tag("("), hexcolor, tag(")"))),
    ))(input)?;

    Ok((
        input,
        Command {
            direction,
            steps,
            color,
        },
    ))
}

// Parse many commands, newline delimited
pub fn commands(input: &str) -> IResult<&str, Vec<Command>> {
    separated_list1(newline, command)(input)
}
```

### Solution

We have the input, let's use a `Grid` to store the hole we're digging:

```rust
fn main() -> Result<()> {
    let stdin = io::stdin();
    let input = io::read_to_string(stdin.lock())?;
    let (s, commands) = parse::commands(&input).unwrap();
    assert_eq!(s.trim(), "");

    let mut hole = Grid::default();
    let mut current = Point::ORIGIN;

    hole.insert(current, true);

    commands.iter().for_each(|c| {
        for _ in 0..c.steps {
            current = current + Point::from(c.direction);
            hole.insert(current, true);
        }
    });

    // Find the first point 'inside' the hole
    let inside = Point::new(
        commands
            .iter()
            .find_map(|c| match c.direction {
                Direction::Left => Some(-1),
                Direction::Right => Some(1),
                _ => None,
            })
            .unwrap(),
        commands
            .iter()
            .find_map(|c| match c.direction {
                Direction::Up => Some(-1),
                Direction::Down => Some(1),
                _ => None,
            })
            .unwrap(),
    );

    hole.flood_fill(inside, true);

    let result = hole.len();
    println!("{result}");
    Ok(())
}
```

Two interesting points there. To find the 'inside' of the shape we're drawing, look for the first horizontal and first vertical line we're drawing. Assume that's an inside corner. Then we take the new [flood fill](#adding-flood-fill-to-grid) method and away we go!

### Adding flood fill to Grid

```rust
impl<T: Copy + Clone> Grid<T> {
    // Flood fill points not currently in the grid with the given value
    // Will not extend bounds
    pub fn flood_fill(&mut self, pt: Point, arg: T) {
        let mut stack = vec![pt];

        while let Some(pt) = stack.pop() {
            assert!(self.bounds.contains(&pt));

            if self.get(&pt).is_none() {
                self.insert(pt, arg);
                stack.push(pt + Point::new(0, 1));
                stack.push(pt + Point::new(0, -1));
                stack.push(pt + Point::new(1, 0));
                stack.push(pt + Point::new(-1, 0));
            }
        }
    }
}
```

It does require `Copy` (and thus `Clone`) since we're filling in the same `arg` in each point, but I really like how this just works!

## Part 2

> The original input included six character hex values. Use those as direction + distance where the first 5 characters are the hex encoded distance and the last one is the direction (`0123` as `RDLU`). 

Well, that's not bad is it? Just rewrite the `Commands`:

```rust
commands.iter_mut().for_each(|c| {
    let s = c.color.to_hex();
    c.steps = u64::from_str_radix(&s[1..6], 16).unwrap();
    c.direction = match s.chars().last().unwrap() {
        '0' => Direction::Right,
        '1' => Direction::Down,
        '2' => Direction::Left,
        '3' => Direction::Up,
        _ => panic!("Invalid direction"),
    }
});
```

Like I said, it's kind of funny that we ended up decoding those hex values, since that made this a bit weirder. 

Run it and... there goes all my RAM. 

Yeah. That's not going to work. 

### Using MATH

So we have a [[wiki:polygon]]() right? There has to be some sort of algorithm that can just turn that into an area. 

Turns out, yes! [This article](https://www.mathopenref.com/coordpolygonarea.html) from openmathref.org gives almost exactly what we need. 

```rust
// Find the vertexes, make sure we're 'closed' by including the origin at both ends
let mut vertexes = vec![];
vertexes.push(Point::ORIGIN);

let mut current = Point::ORIGIN;
commands.iter().for_each(|c| {
    current = current + (c.steps as isize) * Point::from(c.direction);
    vertexes.push(current);
});
vertexes.push(Point::ORIGIN);

// https://www.mathopenref.com/coordpolygonarea.html
let mut result = vertexes
    .iter()
    .tuple_windows()
    .map(|(a, b)| a.x * b.y - a.y * b.x)
    .sum::<isize>()
    / 2;
```

The problem with that is that we're dealing with entire points on the `Grid`, not just `Points` in space. So we need to include the walls. But only half of them, so count `left` and `up` (doesn't matter so long as it's one horizontal and one vertical). 

```rust
// Since we want the border, add half of them (all left and up, it's arbitrary)
result += commands
    .iter()
    .map(|c| {
        if c.direction == Direction::Left || c.direction == Direction::Up {
            c.steps as isize
        } else {
            0
        }
    })
    .sum::<isize>();
```

And then... for some reason I'm still not entirely sure about ... we're always off by exactly 1. 

```rust
// Final result is always off by 1 for reasons? 
result += 1;
```

I expect it has to be with including `Point::ORIGIN` at the beginning and the end, but I'm not entirely sure. I tested with both part 1 and part 2 and tests and not, it's always off by this 1. So add 1 and away we go!


## Performance

The original solution applied to part 2 never did finish, so instead, here are the faster solutions (including solving part 1 with the `vertex` method):

```bash
$ just time 18 1

hyperfine --warmup 3 'just run 18 1'
Benchmark 1: just run 18 1
  Time (mean ± σ):     106.3 ms ±  13.0 ms    [User: 39.7 ms, System: 17.9 ms]
  Range (min … max):    95.7 ms … 143.2 ms    20 runs

$ just time 18 1-vertex

hyperfine --warmup 3 'just run 18 1-vertex'
Benchmark 1: just run 18 1-vertex
  Time (mean ± σ):     190.2 ms ± 112.6 ms    [User: 44.5 ms, System: 22.6 ms]
  Range (min … max):   101.0 ms … 517.8 ms    18 runs

$ just time 18 2

hyperfine --warmup 3 'just run 18 2'
Benchmark 1: just run 18 2
  Time (mean ± σ):     174.0 ms ±  64.4 ms    [User: 42.4 ms, System: 22.3 ms]
  Range (min … max):   109.6 ms … 276.4 ms    11 runs
```

I did find it interesting that the `vertex` solution is slower for part 1, but it's doing a decent amount of extra work to save (gigabytes of) RAM, so it makes sense. If part 2 ever finished I can guarantee that one would have been faster with this solution. 

Once again, onward!