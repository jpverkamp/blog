---
title: "AoC 2024 Day 15: Sokobaninator"
date: 2024-12-15 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Sokoban
- Iterators
---
## Source: [Day 15: Warehouse Woes](https://adventofcode.com/2024/day/15)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day15.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> Given a warehouse containing floors (`.`), walls (`#`), boxes (`O`), and the player (`@`) plus a series of instructions `^V<>`, move the player according to the instructions, pushing boxes (which in turn can push more boxes).
>
> Calculate the sum of `y * 100 + x` for each box's final position. 

<!--more-->

I've totally done this a number of times in [[Rust Solvers]](). And it's even easier here, since the blocks don't stick together into arbitrarily large shapes!

Okay, first our representation:

```rust
#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
enum Tile {
    #[default]
    Empty,
    Wall,
    Box,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct State {
    tiles: Grid<Tile>,
    position: Point,
    instructions: Vec<Direction>,
    index: usize,
}
```

And parser:

```rust
#[aoc_generator(day15)]
pub fn parse(input: &str) -> State {
    let (tile_data, instruction_data) = input.split_once("\n\n").unwrap();

    let tiles = Grid::read(tile_data, &|c| match c {
        '#' => Tile::Wall,
        '.' => Tile::Empty,
        'O' => Tile::Box,
        '@' => Tile::Empty,
        _ => panic!("unexpected character"),
    });

    let position_index = tile_data.chars().position(|c| c == '@').unwrap() as i32;
    let newline_width = tiles.width + 1;
    let position = (
        position_index % newline_width as i32,
        position_index / newline_width as i32,
    )
        .into();

    let instructions = instruction_data
        .chars()
        .filter_map(|c| match c {
            'v' => Some(Direction::Down),
            '^' => Some(Direction::Up),
            '<' => Some(Direction::Left),
            '>' => Some(Direction::Right),
            _ => None,
        })
        .collect();

    State {
        tiles,
        position,
        instructions,
        index: 0,
    }
}
```

Seems straight forward enough. Eating extra characters with `_ => None` handles the cases of a trailing newline or not, but it did bite me when it came to some tests. So it goes. 

Okay, now I'm actually going to put a lot of methods on `impl State` here rather than putting them in the problem description. Let's start at the 'top' by turning `State` into an iterator:

```rust
impl Iterator for State {
    type Item = (Direction, Point);

    fn next(&mut self) -> Option<Self::Item> {
        if self.index >= self.instructions.len() {
            return None;
        }

        let direction = self.instructions[self.index];
        self.index += 1;

        let new_position = self.position + direction;

        if self.can_move(self.position, direction) {
            self.push(new_position, direction);
            self.position = new_position;
        }

        Some((direction, self.position))
    }
}
```

That's straight forward enough. As long as there are more instructions, keep going along on them. If you `can_move` (which needs to make sure if you're moving into a box it can push anything on the other side of it recursively), then do the push (which does nothing if it's `Empty`), then move ourselves. 

There is a downside in that every move will recur twice: once for `can_move` and again for `push`. If there are a ton of blocks all moving together, this is relatively expensive, but it will save us a bunch of special cases in [the long run](#part-2). 

Okay, so what is `can_move`?

```rust
impl State {
    fn can_move(&self, position: Point, direction: Direction) -> bool {
        let new_position = position + direction;

        match self.tiles.get(new_position) {
            Some(Tile::Wall) | None => false,
            Some(Tile::Empty) => true,
            Some(Tile::Box) => self.can_move(new_position, direction),
        }
    }
}
```

That really is it. 

And `push` isn't much more complicated:

```rust
impl State {
    fn push(&mut self, position: Point, direction: Direction) {
        // WARN: Assumes that it's safe to push!!

        let new_position = position + direction;

        match self.tiles.get(position) {
            // Walls and empty spaces don't move
            Some(Tile::Wall) | Some(Tile::Empty) | None => {}

            Some(Tile::Box) => {
                self.push(new_position, direction);
                self.tiles.set(new_position, Tile::Box);
                self.tiles.set(position, Tile::Empty);
            }
        }
    }
}
```

Add in a score function:

```rust
impl State {
    fn score(&self) -> usize {
        self.tiles
            .iter_enumerate()
            .map(|(p, t)| match t {
                Tile::Box => p.y as usize * 100 + p.x as usize,
                _ => 0,
            })
            .sum()
    }
}
```

And that's it!

```rust
#[aoc(day15, part1, v1)]
fn part1_v1(input: &State) -> usize {
    let mut state = input.clone();

    for (_d, _p) in state.by_ref() {
        // Do nothing, the iterator does all the work
    }

    state.score()
}
```

Whee!

```bash
$ cargo aoc --day 15 --part 1

AOC 2024
Day 15 - Part 1 - v1 : 1552879
	generator: 154.125µs,
	runner: 266.916µs
```

Here's a rendering of the little thing in action:

<video controls src="/embeds/2024/aoc/day15-part1.mp4"></video>

That's at 10x speed (that's why it jumps around so much)... the original rendering of the whole thing was *quite* a bit longer/larger. 

## Part 2

> Make the initial input WIDER. For each wall or space, make it two walls or spaces. For each box, replace it with a BIG BOX (`[]`). This should move together and either half can push:
>
> ```text
> ......
> ..[]..
> ...[].
> ..[]..
> ..@...
> ```
>
> Moving `^` should push the whole mess. 
>
> The scoring function remains the same, just use the left half of the box. 

Cool. 

```rust
impl State {
    pub fn clone_but_wider(&self) -> State {
        let mut new_tiles = Grid::new(self.tiles.width * 2, self.tiles.height);

        for y in 0..self.tiles.height {
            for x in 0..self.tiles.width {
                let tile = self.tiles.get((x, y)).unwrap();

                let (left, right) = match tile {
                    Tile::Wall | Tile::Empty => (*tile, *tile),
                    Tile::Box | Tile::BigBoxLeft | Tile::BigBoxRight => {
                        (Tile::BigBoxLeft, Tile::BigBoxRight)
                    }
                };

                new_tiles.set((x * 2, y), left);
                new_tiles.set((x * 2 + 1, y), right);
            }
        }

        let new_position = (self.position.x * 2, self.position.y).into();

        State {
            tiles: new_tiles,
            position: new_position,
            instructions: self.instructions.clone(),
            index: self.index,
        }
    }
}
```

I mostly just wanted a function named `clone_but_wider`. :smile:

We do need to update all of the functions above to include some new state. I'm going to add `BigBoxLeft` and `BigBoxRight` as two separate tiles and make sure in the code that we don't split them up. It's imperfect (I did have a case where they started splitting in half), but I think it's probably the easiest way to go. 

```rust
#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tile {
    #[default]
    Empty,
    Wall,
    Box,
    BigBoxLeft,
    BigBoxRight,
}

impl State {
    pub fn clone_but_wider(&self) -> State {
        let mut new_tiles = Grid::new(self.tiles.width * 2, self.tiles.height);

        for y in 0..self.tiles.height {
            for x in 0..self.tiles.width {
                let tile = self.tiles.get((x, y)).unwrap();

                let (left, right) = match tile {
                    Tile::Wall | Tile::Empty => (*tile, *tile),
                    Tile::Box | Tile::BigBoxLeft | Tile::BigBoxRight => {
                        (Tile::BigBoxLeft, Tile::BigBoxRight)
                    }
                };

                new_tiles.set((x * 2, y), left);
                new_tiles.set((x * 2 + 1, y), right);
            }
        }

        let new_position = (self.position.x * 2, self.position.y).into();

        State {
            tiles: new_tiles,
            position: new_position,
            instructions: self.instructions.clone(),
            index: self.index,
        }
    }

    fn can_move(&self, position: Point, direction: Direction) -> bool {
        let new_position = position + direction;

        match self.tiles.get(new_position) {
            Some(Tile::Wall) | None => false,
            Some(Tile::Empty) => true,
            Some(Tile::Box) => self.can_move(new_position, direction),

            // Big boxes always act as the left half to avoid duplication
            Some(Tile::BigBoxLeft) => match direction {
                Direction::Up | Direction::Down => {
                    self.can_move(new_position, direction)
                        && self.can_move(new_position + Direction::Right, direction)
                }
                Direction::Left => self.can_move(new_position, direction),
                Direction::Right => self.can_move(new_position + Direction::Right, direction),
            },
            Some(Tile::BigBoxRight) => self.can_move(position + Direction::Left, direction),
        }
    }

    fn push(&mut self, position: Point, direction: Direction) {
        // WARN: Assumes that it's safe to push!!

        let new_position = position + direction;

        match self.tiles.get(position) {
            // Walls and empty spaces don't move
            Some(Tile::Wall) | Some(Tile::Empty) | None => {}

            Some(Tile::Box) => {
                self.push(new_position, direction);
                self.tiles.set(new_position, Tile::Box);
                self.tiles.set(position, Tile::Empty);
            }

            // Big boxes always act as the left half to avoid duplication
            Some(Tile::BigBoxLeft) => match direction {
                Direction::Up | Direction::Down => {
                    self.push(new_position, direction);
                    self.push(new_position + Direction::Right, direction);
                    self.tiles.set(new_position, Tile::BigBoxLeft);
                    self.tiles
                        .set(new_position + Direction::Right, Tile::BigBoxRight);
                    self.tiles.set(position, Tile::Empty);
                    self.tiles.set(position + Direction::Right, Tile::Empty);
                }
                Direction::Left => {
                    self.push(new_position, direction);
                    self.tiles.set(new_position, Tile::BigBoxLeft);
                    self.tiles.set(position, Tile::BigBoxRight);
                    self.tiles.set(position + Direction::Right, Tile::Empty);
                }
                Direction::Right => {
                    self.push(new_position + Direction::Right, direction);
                    self.tiles
                        .set(new_position + Direction::Right, Tile::BigBoxRight);
                    self.tiles.set(new_position, Tile::BigBoxLeft);
                    self.tiles.set(position, Tile::Empty);
                }
            },
            Some(Tile::BigBoxRight) => {
                self.push(position + Direction::Left, direction);
            }
        }
    }

    fn score(&self) -> usize {
        self.tiles
            .iter_enumerate()
            .map(|(p, t)| match t {
                Tile::Box | Tile::BigBoxLeft => p.y as usize * 100 + p.x as usize,
                _ => 0,
            })
            .sum()
    }
}
```

One trick I did use is, rather than duplicating code between `BigBoxLeft` and `BixBoxRight`, I will always take the `BigBoxRight` case and turn it into a `BigBoxLeft` one tile over. It's still crazier code, but compared to some other things (boxes sticking together, splitting apart, and getting swung around)... this is nothing much. 

All this means though is:

```rust
#[aoc(day15, part2, v1)]
fn part2_v1(input: &State) -> usize {
    let mut state = input.clone_but_wider();

    for (_d, _p) in state.by_ref() {
        // Do nothing, the iterator does all the work
    }
   
    state.score()
}
```

That... really is the only change!

```bash 
$ cargo aoc --day 15 --part 2

AOC 2024
Day 15 - Part 2 - v1 : 1561175
	generator: 156.459µs,
	runner: 298.166µs
```

And it's only marginally slower! Mostly because the big boxes when moving up or down can trigger a pair of other things to move, which can cascade a bit plus some more work to handle the `Right/Left` shift. But really, sub-ms is absolutely fine by me!

Here's the video:

<video controls src="/embeds/2024/aoc/day15-part2.mp4"></video>

And if you'd like to watch the two versions head to head:

<video controls src="/embeds/2024/aoc/day15.mp4" width="100%"></video>

It's interesting to watch them diverge (since there's more width to cover) and then come back together (as I expect they run into things to sync back up). 

## WIIIIIIIIDER

```rust
input.clone_but_wider().clone_but_wider()
```

<video controls src="/embeds/2024/aoc/day15-part2plus.mp4"></video>

That is all. 

## Benchmarks

```bash
$ cargo aoc bench --day 15

Day15 - Part1/v1        time:   [236.85 µs 238.71 µs 242.12 µs]
Day15 - Part2/v1        time:   [280.64 µs 282.88 µs 286.44 µs]
```