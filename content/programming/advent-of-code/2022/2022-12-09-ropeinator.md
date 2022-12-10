---
title: "AoC 2022 Day 9: Ropeinator"
date: 2022-12-09 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Rope Bridge](https://adventofcode.com/2022/day/9)

#### **Part 1:** Simulate two connected links such that whenever the first link (head) moves, the tail moves to follow according to the following rules:

* If the tail is at the same location as head, don't move
* If the tail is adjacent to the head (orthogonal or diagonal), don't move
* If the tail is in the same row/column as the head, move one directly towards it orthogonally
* If the tail is in neither the same row nor column, move one towards diagonally

Count how many unique spaces are visited by the `tail` of the link. 

<!--more-->

Okay. I went a bit overboard this with structures. But what else is new. 

First, let's introduce a `Point` to our standard AoC library:

```rust

#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash)]
pub struct Point {
    pub x: isize,
    pub y: isize,
}

impl Point {
    pub fn manhattan_distance(&self, other: &Point) -> isize {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }

    pub fn adjacent_to(&self, other: &Point) -> bool {
        self.manhattan_distance(other) == 1
            || ((self.x - other.x).abs() == 1 && (self.y - other.y).abs() == 1)
    }
}

impl Point {
    pub const ORIGIN: Point = Point { x: 0, y: 0 };
}

impl Add for Point {
    type Output = Self;

    fn add(self, rhs: Self) -> Self::Output {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
        }
    }
}

impl Sub for Point {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self::Output {
        Point {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
        }
    }
}
```

We'll probably need some more helpers, but for now, this should be enough. 

One thing to note is that I'm currently working on an immutable/copy on modify design. When you add two `Point`, you get a new `Point`. I'm going to end up carrying that through the entire program today. 

Okay next, we're going to get the input as a series of `[UDLR] \d` patterns. So we want something that can represent a `Direction` and turn that into a `Point` to add to our current position:

```rust
/* ----- Implement orthogonal directions ----- */
#[derive(Copy, Clone, Debug)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

impl From<char> for Direction {
    fn from(c: char) -> Self {
        match c {
            'U' => Direction::Up,
            'D' => Direction::Down,
            'L' => Direction::Left,
            'R' => Direction::Right,
            _ => panic!("unknown direction char"),
        }
    }
}

impl Direction {
    fn delta(self) -> Point {
        match self {
            Direction::Up => Point { x: 0, y: -1 },
            Direction::Down => Point { x: 0, y: 1 },
            Direction::Left => Point { x: -1, y: 0 },
            Direction::Right => Point { x: 1, y: 0 },
        }
    }
}
```

Next, we can combine that with the distance for a full `Instruction`:

```rust
/* ----- Store a single instruction: direction + distance ----- */
#[derive(Copy, Clone, Debug)]
struct Instruction {
    direction: Direction,
    distance: usize,
}

impl From<String> for Instruction {
    fn from(line: String) -> Self {
        let mut parts = line.split_ascii_whitespace();

        let direction = Direction::from(
            parts
                .next()
                .expect("must have a direction part")
                .chars()
                .nth(0)
                .expect("must have a "),
        );

        let distance = parts
            .next()
            .expect("must have a number part")
            .parse::<usize>()
            .expect("number must be a number");

        Instruction {
            direction,
            distance,
        }
    }
}
```

I'm really liking how the `cargo fmt` chained methods work in Rust. I went back and formatted the old code, but I only really even noticed that that was a thing. 

Okay, we have instructions, so it's probably about time to implement the actual `Rope`, no?

```rust
use im::HashSet;

/* ----- Implement a one link rope ----- */
#[derive(Clone, Debug)]
struct Rope {
    head: Point,
    tail: Point,
    visited: HashSet<Point>,
}

impl Rope {
    // Initialize a new rope coiled at the origin
    fn new() -> Self {
        Rope {
            head: Point::ORIGIN,
            tail: Point::ORIGIN,
            visited: HashSet::unit(Point::ORIGIN),
        }
    }

    // Step n times in one direction
    fn step_by(self, instruction: Instruction) -> Self {
        let mut current = self;

        for _ in 0..instruction.distance {
            let new_head = current.head + instruction.direction.delta();
            let new_tail = current.tail.follow(new_head);

            let mut new_visited = current.visited;
            new_visited.insert(new_tail);

            current = Rope {
                head: new_head,
                tail: new_tail,
                visited: new_visited,
            };
        }

        current
    }
}
```

You'll note that I once again created a new `Rope` and returned it, rather than modifying `self`. That's sort of implicit in the `Clone` trait and `let mut current = self` forcing a copy, I suppose? 

One big thing to note is that if I were using the `std::HashSet` this wouldn't have worked. That doesn't implement `clone`, since it's expensive to copy a hash set. Instead, I broke my previous rule to starting using the [`im` crate](https://crates.io/crates/im). It is a set of immutable data structures for Rust that are designed the same more functional languages are: the underlying data structure is shared and mutations are mady by `clone` + modify the new version. So you get `clone`. Not something I wanted to implement by hand. 

Finally, you might be wondering about `follow`. That's not a method on `Point`... Well, originally, I had `step_by` calling a separate function `step` `n` times because for each of those steps, I would check each of the cases outlined at the top of this post (same spot, adjacent, same row, same column, and diagonal). But then as I was implementing the diagonal case, I noticed something interesting:

```rust
trait Followable {
    fn follow(self, other: Self) -> Self;
}

impl Followable for Point {
    fn follow(self, other: Point) -> Self {
        if self == other || self.adjacent_to(&other) {
            self
        } else {
            let xd = (other.x - self.x).signum();
            let yd = (other.y - self.y).signum();

            self + Point { x: xd, y: yd }
        }
    }
}
```

Ignore the `Followable` for a minute and just focus on the new method `follow` on a `Point`. `signum` will return the sign of the difference (or 0 if they're the same). So in those above cases:

* Tail = head and adjacent, special cases, don't move
* Same row, `xd` = 1 in the direction to move in the x, `yd = 0` because they're the same
* Same column, `yd` = 1 in the direction to move in the, `xd = 0` because they're the same
* In the diagonal cases, we want each of `xd` and `yd` to be non-zero (which they will be because the differences are non-zero) and they'll point in the right direction because of signum

I could probably explain that better, but the long and the short of it is, that's *exactly* what we need to step. 

Back one step to why I introduced a new `Followable` trait: that's by design. You can't add a method to an `impl` from another crate, which is the case here (I have a `aoc` crate for the library functions). Instead, you can add a trait in this crate and them `impl` *that* just in this crate. No one else needs to worry about it, which is handy if they happened to want to introduce something with the same name that behaved differently. 

Rust is neat. 

Okay, with `Instruction::from` handling parsing and `Rope::step_by` handling movement, that should be everything we need to solve the problem:

```rust
fn part1(filename: &Path) -> String {
    let mut rope = Rope::new();

    for line in iter_lines(filename) {
        let instruction = Instruction::from(line);
        rope = rope.step_by(instruction);
    }

    rope.visited.len().to_string()
}
```

And that's it. Voila. 

#### **Part 2:** Increase the number of linked elemnts to 10. Count how many unique spaces the last element of the chain visits. 

Now that's an interesting twist. Originally, I wanted to do something like this:

```rust
struct Chain {
    ropes: Vec<Rope>,
}
```

But try as I wanted, I just couldn't get that working. I think it was fact that `Rope` is `Clone`, but not `Copy` (because of the `HashSet`). So in the end, I instead generalized the `Vec<Point>`:

```rust
/* ----- For part 2, generalize to chains of any length ----- */
#[derive(Clone, Debug)]
struct Chain {
    points: Vec<Point>,
    tail_visited: HashSet<Point>,
}

impl Chain {
    fn new(size: usize) -> Self {
        Chain {
            points: vec![Point::ORIGIN; size],
            tail_visited: HashSet::unit(Point::ORIGIN),
        }
    }

    fn step_by(self, instruction: Instruction) -> Self {
        let mut current = self.clone();

        for _ in 0..instruction.distance {
            let mut new_points = Vec::new();
            let mut previous = current.points[0] + instruction.direction.delta();

            new_points.push(previous);

            for point in current.points.iter().skip(1) {
                let next = point.follow(previous);
                new_points.push(next);
                previous = next;
            }

            let mut new_tail_visited = current.tail_visited;
            new_tail_visited.insert(previous);

            current = Chain {
                points: new_points,
                tail_visited: new_tail_visited,
            }
        }

        current
    }
}
```

The code is a bit more complicated, but the general idea is the same. This time, for each movement, we're going to:

* Initialize the new head of the rope by moving as before, store this as `previous`
* For each remaining node of the chain, `follow` the `previous` node, then store that moved value in the chain + in `previous`

This actually worked pretty elegantly if I do say so myself. And it let's me do the same thing by using the last value of `previous` to store in the `HashSet` of visited points. 

For `part2`:

```rust
fn part2(filename: &Path) -> String {
    let mut chain = Chain::new(10);

    for line in iter_lines(filename) {
        let instruction = Instruction::from(line);
        chain = chain.step_by(instruction);
    }

    chain.tail_visited.len().to_string()
}
```

Not even any longer!

One neat thing is that you can actually use this to solve `part1` as well, which I do when `debug_assertions` is enabled:

```rust
fn part1(filename: &Path) -> String {
    let mut rope = Rope::new();

    for line in iter_lines(filename) {
        let instruction = Instruction::from(line);
        rope = rope.step_by(instruction);
    }

    if cfg!(debug_assertions) {
        let mut chain = Chain::new(2);

        for line in iter_lines(filename) {
            let instruction = Instruction::from(line);
            chain = chain.step_by(instruction);
        }

        println!("using a chain(2): {}", chain.tail_visited.len());
    }

    rope.visited.len().to_string()
}
```

Mostly, to verify that both do the same thing, which of course they do. 

One thing that I kind of want to do is visualize this, but it's already been a long day. Perhaps I'll work it out another day. 

#### Performance

```bash
$ ./target/release/09-ropeinator 1 data/09.txt

6339
took 3.278708ms

$ ./target/release/09-ropeinator 2 data/09.txt

2541
took 8.009958ms
```

Still only fractions of a second. :smile: 

Rust is fun. 