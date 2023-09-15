---
title: "AoC 2022 Day 22: Wonderator"
date: 2022-12-22 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- Algorithms
- Visualization
---
## Source: [Monkey Map](https://adventofcode.com/2022/day/22)

## Part 1

> Given a map and a series of instructions formatted as distance + turn (`L` or `R`), find the final position. Any time you would walk off the edge of the map, wrap to the opposite edge. 

<!--more-->

Well that's fun. Let's load the map first:

```rust
#[derive(Debug)]
struct Map {
    start: Point,
    width: usize,
    height: usize,
    walls: HashSet<Point>,
    floors: HashSet<Point>,
    path_data: Vec<(Point, char)>,
}

impl<I> From<&mut I> for Map
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        let mut walls = HashSet::new();
        let mut floors = HashSet::new();
        let mut width = 0;
        let mut height = 0;
        let mut start: Option<Point> = None;

        iter.take_while(|line| !line.is_empty())
            .enumerate()
            .for_each(|(y, line)| {
                height = height.max(y + 1);
                line.chars().enumerate().for_each(|(x, c)| match c {
                    '#' => {
                        width = width.max(x + 1);
                        walls.insert(Point::new(x as isize + 1, y as isize + 1));
                    }
                    '.' => {
                        if start.is_none()
                            || y as isize + 1 < start.unwrap().y
                            || (y as isize + 1 <= start.unwrap().y
                                && x as isize + 1 < start.unwrap().x)
                        {
                            start = Some(Point::new(x as isize + 1, y as isize + 1));
                        }

                        width = width.max(x + 1);
                        floors.insert(Point::new(x as isize + 1, y as isize + 1));
                    }
                    _ => {}
                })
            });

        Map {
            start: start.unwrap(),
            width,
            height,
            walls,
            floors,
            path_data: vec![(start.unwrap(), '>')],
        }
    }
}
```

I'm again using `HashSets` to store (relatively) sparse point data. Storing it in a single vector and accessing it would probably be as quick if not quicker with caching and direct `O(1)` access, but this is perfectly fine for what I'm working on. 

Next up, parsing and storing the list of moves:

```rust
#[derive(Debug)]
struct Moves {
    data: Vec<(usize, char)>,
}

impl From<String> for Moves {
    fn from(line: String) -> Self {
        let iter = &mut line.chars().peekable();
        let mut data = Vec::new();

        while !iter.peek().is_none() {
            // Distance is a positive integer, might be more than one digit
            let distance = iter
                .peeking_take_while(|c| c.is_digit(10))
                .collect::<String>()
                .parse::<usize>()
                .expect("must be parsable as a number");

            // Parse L or R as a turn, add an L at the end if we end with a number
            let turn = if iter.peek().is_some() {
                iter.next().unwrap()
            } else {
                'X'
            };

            data.push((distance, turn));
        }

        Moves { data }
    }
}
```

The one oddity here is that the original problem doesn't have a last turn in the test data, but the final scoring requested relies on a turn. So I added a `X` 'don't turn' instruction. 

Lastly, we'll have one more `struct` that represents which way we're currently `Facing`:

```rust
#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
enum Facing {
    North,
    South,
    East,
    West,
}

impl Default for Facing {
    fn default() -> Self {
        Facing::East
    }
}

impl Facing {
    fn turn(self, turn: char) -> Self {
        use Facing::*;

        match (self, turn) {
            (North, 'L') => West,
            (North, 'R') => East,
            (South, 'L') => East,
            (South, 'R') => West,

            (East, 'L') => North,
            (East, 'R') => South,
            (West, 'L') => South,
            (West, 'R') => North,

            (_, 'X') => self,

            _ => panic!("don't know how to turn {turn} from {self:?}"),
        }
    }

    fn opposite(self) -> Self {
        use Facing::*;

        match self {
            North => South,
            South => North,
            East => West,
            West => East,
        }
    }

    fn delta(self) -> Point {
        use Facing::*;

        match self {
            North => Point::new(0, -1),
            South => Point::new(0, 1),
            East => Point::new(1, 0),
            West => Point::new(-1, 0),
        }
    }

    fn char(&self) -> char {
        use Facing::*;

        match self {
            North => '^',
            South => 'v',
            East => '>',
            West => '<',
        }
    }

    fn value(&self) -> isize {
        use Facing::*;

        match self {
            East => 0,
            South => 1,
            West => 2,
            North => 3,
        }
    }
}
```

Basically, this is the cardinal direction and you can apply the `L` and `R` to this to get a new facing plus you can get the `value` for scoring that I mentioned or the `delta` for how you should move. 

Take all that and we're ready to apply a `Move` to the `Map`:

```rust
impl Map {
    fn calculate_move(
        &mut self,
        location: Point,
        facing: Facing,
        distance: usize,
    ) -> Point {
        let mut current = location;
        self.path_data.push(current);

        for _i in 0..distance {
            let mut next = current + facing.delta();

            // If we run into a wall, just stop moving
            if self.walls.contains(&next) {
                break;
            }

            // If we run off the map, wrap
            if !self.floors.contains(&next) {
                // Step back onto the floor
                next = current;

                // Skip back across the walls and floors this time
                while self.floors.contains(&next) || self.walls.contains(&next) {
                    next = next - facing.delta();
                }

                // Step back once off empty space
                next = next + facing.delta();

                // If we have a wall after wrapping, don't move
                if self.walls.contains(&next) {
                    break;
                }
            }

            // If we made it out of both checks, we have the new current point
            self.path_data.push((current));
            current = next;
        }

        current
    }
}
```

Fairly clean. Wrap it up and off we go:

```rust
fn part1(filename: &Path) -> String {
    let mut iter = &mut iter_lines(filename);
    let mut map = Map::from(&mut iter);
    let moves = Moves::from(iter.next().expect("must have moves"));

    let mut location = map.start.clone();
    let mut facing = Facing::East;

    let move_count = moves.data.len();
    for (frame, (distance, turn)) in moves.data.into_iter().enumerate() {
        location = map.calculate_move(location, facing, distance);
        facing = facing.turn(turn);
    }

    let password = 1000 * location.y + 4 * location.x + facing.value();
    password.to_string()
}
```

Not so bad. One fun thing that I did was to make a rendering function ([see below]({{<ref "#writing-a-rendering-function">}}) so that I could generate fun animations like this:

<video controls src="/embeds/2022/aoc22-1-red.mp4"></video>

Or more colorful (the 4 different colors are the facings):

<video controls src="/embeds/2022/aoc22-1-colorful.mp4"></video>

Did it help solve the problem? Nope. Printing to the console was better for that. Is it fun to watch? Absolutely! (Especially with the paths fading over time.)

## Part 2

> Instead of wrapping around to the next edge, fold the map you are given into a cube and proceed onto the next face. Calculate the final position as before. 

...

{{< figure height="400px" src="/embeds/2022/aoc22-papercraft.jpg" >}}

{{< figure height="400px" src="/embeds/2022/aoc22-cubular.jpg" >}}

Why yes. I did make a physical cube in order to figure out how all of the different adjacencies work:

```rust
fn part2(filename: &Path) -> String {
    let mut iter = &mut iter_lines(filename);
    let mut map = Map::from(&mut iter);
    let moves = Moves::from(iter.next().expect("must have moves"));

    let mut location = map.start.clone();
    let mut facing = Facing::East;

    use Facing::*;

    let test_mode = filename.to_str().unwrap().contains("test");

    let size = if test_mode { 4 } else { 50 };
    let adjacency_map: HashMap<(Point, Facing), (Point, Facing)> = (if test_mode {
        let faces = [
            Point::new(2, 0),
            Point::new(0, 1),
            Point::new(1, 1),
            Point::new(2, 1),
            Point::new(2, 2),
            Point::new(3, 2),
        ];

        // Hand calculated for the test map
        // TODO: Can this be automated?
        vec![
            ((faces[1 - 1], West), (faces[3 - 1], South)),
            ((faces[1 - 1], North), (faces[2 - 1], South)),
            ((faces[1 - 1], East), (faces[6 - 1], West)),
            ((faces[2 - 1], North), (faces[1 - 1], South)),
            ((faces[2 - 1], West), (faces[6 - 1], North)),
            ((faces[2 - 1], South), (faces[5 - 1], North)),
            ((faces[3 - 1], North), (faces[1 - 1], East)),
            ((faces[3 - 1], South), (faces[5 - 1], East)),
            ((faces[4 - 1], East), (faces[6 - 1], South)),
            ((faces[5 - 1], West), (faces[3 - 1], North)),
            ((faces[5 - 1], South), (faces[2 - 1], North)),
            ((faces[6 - 1], North), (faces[4 - 1], West)),
            ((faces[6 - 1], East), (faces[1 - 1], West)),
            ((faces[6 - 1], South), (faces[2 - 1], East)),
        ]
    } else {
        let faces = [
            Point::new(1, 0),
            Point::new(2, 0),
            Point::new(1, 1),
            Point::new(0, 2),
            Point::new(1, 2),
            Point::new(0, 3),
        ];

        // Hand calculated for my map
        // TODO: Can this be automated?
        vec![
            ((faces[1 - 1], North), (faces[6 - 1], East)),
            ((faces[1 - 1], West), (faces[4 - 1], East)),
            ((faces[2 - 1], North), (faces[6 - 1], North)),
            ((faces[2 - 1], East), (faces[5 - 1], West)),
            ((faces[2 - 1], South), (faces[3 - 1], West)),
            ((faces[3 - 1], West), (faces[4 - 1], South)),
            ((faces[3 - 1], East), (faces[2 - 1], North)),
            ((faces[4 - 1], North), (faces[3 - 1], East)),
            ((faces[4 - 1], West), (faces[1 - 1], East)),
            ((faces[5 - 1], East), (faces[2 - 1], West)),
            ((faces[5 - 1], South), (faces[6 - 1], West)),
            ((faces[6 - 1], West), (faces[1 - 1], South)),
            ((faces[6 - 1], East), (faces[5 - 1], North)),
            ((faces[6 - 1], South), (faces[2 - 1], South)),
        ]
    })
    .into_iter()
    .collect();

    for (pf1, pf2) in adjacency_map.iter() {
        let pf1p = (pf1.0, pf1.1.opposite());
        let pf2p = (pf2.0, pf2.1.opposite());

        if !adjacency_map.contains_key(&pf2p) {
            panic!("Expecing {pf2p:?} in adjacency_map to match {pf2:?}");
        }

        if adjacency_map[&pf2p] != pf1p {
            panic!(
                "Expecing value of {pf2p:?} to be {pf1p:?}, got {:?}",
                adjacency_map[&pf2p]
            );
        }
    }

    let wrap_mode = WrapMode::Cube(size, adjacency_map);

    let move_count = moves.data.len();
    for (frame, (distance, turn)) in moves.data.into_iter().enumerate() {
        (location, facing) = map.calculate_move(location, facing, distance, &wrap_mode);
        facing = facing.turn(turn);
    }

    let password = 1000 * location.y + 4 * location.x + facing.value();
    password.to_string()
}
```

And yes, I did handcode the adjacency map for both the test cube and my regular cube. What of it? 

:smile:

Making sure that I got everything right took a while. That's why there's the check function in there that `panic!`s if I got something wrong. This works because each edge is bidirectional, just the orientations are flipped. If I ever make a mistake, hopefully I don't make the same (opposite) mistake as well, so it will pop out. I caught 3... 

I expect there's probably a way to automatically do this, first by finding any 90 degree bends and folding those then folding in the rest that are left over, but this was already mind bendy enough. 

As you may have noticed, I also introduced a new `WrapMode` to handle the two different options:

```rust
#[derive(Debug)]
enum WrapMode {
    Loop,
    Cube(usize, HashMap<(Point, Facing), (Point, Facing)>),
}
```

And then, it's *just* a matter of updating the `calculate_move` function:

```rust
impl Map {
    fn calculate_move(
        &mut self,
        location: Point,
        facing: Facing,
        distance: usize,
        wrap_mode: &WrapMode,
    ) -> (Point, Facing) {
        use Facing::*;

        let mut current = (location, facing);
        self.path_data.push((current.0, current.1.char()));

        for _i in 0..distance {
            let mut next = (current.0 + current.1.delta(), current.1);

            // If we run into a wall, just stop moving
            if self.walls.contains(&next.0) {
                break;
            }

            // If we run off the map, wrap
            if !self.floors.contains(&next.0) {
                // Step back onto the floor
                next = current;

                // Different wrapping options depending on the mode
                match wrap_mode {
                    // Loop is defined as walking the opposite way until you hit an empty space
                    WrapMode::Loop => {
                        // Skip back across the walls and floors this time
                        while self.floors.contains(&next.0) || self.walls.contains(&next.0) {
                            next.0 = next.0 - current.1.delta();
                        }

                        // Step back once off empty space
                        next.0 = next.0 + current.1.delta();
                    }
                    // Cube is defined as wrapping onto the next face of a cube
                    WrapMode::Cube(width, adjacencies) => {
                        // Determine the index of the face
                        let current_face = Point::new(
                            (next.0.x - 1) / (*width as isize),
                            (next.0.y - 1) / (*width as isize),
                        );

                        // Figure out how far we are side to side on that face
                        // Offset is from the 'left' according to facing
                        let current_offset = match facing {
                            North => (next.0.x - 1) % (*width as isize),
                            South => *width as isize - (next.0.x - 1) % (*width as isize) - 1,
                            East => (next.0.y - 1) % (*width as isize),
                            West => *width as isize - (next.0.y - 1) % (*width as isize) - 1,
                        };

                        // Determine the next face and facing
                        let (next_face, next_facing) =
                            adjacencies.get(&(current_face, facing)).expect(
                                format!("unknown adjacency for {current_face:?} facing {facing:?}")
                                    .as_str(),
                            );

                        next = (
                            Point::new(
                                1 + next_face.x * (*width as isize)
                                    + match next_facing {
                                        North => current_offset,
                                        South => *width as isize - current_offset - 1,
                                        East => 0,
                                        West => *width as isize - 1,
                                    },
                                1 + next_face.y * (*width as isize)
                                    + match next_facing {
                                        North => *width as isize - 1,
                                        South => 0,
                                        East => current_offset,
                                        West => *width as isize - current_offset - 1,
                                    },
                            ),
                            *next_facing,
                        );
                    }
                }

                // If we have a wall after wrapping, don't move
                if self.walls.contains(&next.0) {
                    break;
                }
            }

            // If we made it out of both checks, we have the new current point
            self.path_data.push((current.0, current.1.char()));
            current = next;
        }

        current
    }
}
```

Yeah... that's a bit much. 

So a few of the interesting things that I had to end up doing to get cubes working:

* Change `current` to include both `Point` and `Facing`, since `Facing` can now change (multiple times) in the middle of a move if/when you move from one fact to another. 
* Correctly handle the hole `WrapMode::Loop`
* In the new `WrapMode::Cube`:
  * Determine which face we're on (modular arithmetic)
  * Determine how far along that face we are (counting from the 'left' from the perspective of the agent walking around)
  * Determine which face + facing is next, based on the `adjacency_map` from above
  * Figure out what the coordinates in flat space correspond to moving onto the new face
  * Check for a wall and don't make the move if there is one

There are an absolute ton of fiddly bits around this, particularly around making sure that the offset is correct for each of the 4 orientations plus making sure that we correctly offset the maximums by 1 (zero based indexing), but after all that's working, the problem itself (as shown above) doesn't change. 

And we still get pretty videos!

<video controls src="/embeds/2022/aoc22-2-red.mp4"></video>

And more colorful:

<video controls src="/embeds/2022/aoc22-2-colorful.mp4"></video>

It's fun to try to watch it go around the faces of the cube. If I had the time and inclination, I would animate this on the surface of an actual cube (I already have the texture), but that's a problem for another day. 


## Performance

Yet another one where the vast majority of the problem is typing it out:

```bash
$ ./target/release/22-wonderator 1 data/22.txt

196134
took 5.115ms

$ ./target/release/22-wonderator 2 data/22.txt

146011
took 4.83525ms
```

## Writing a rendering function

In case you're wondering, the rendering uses the same basic framework as I did in [[AoC 2022 Day 14: Sandinator]](), just with a rendering function aware of the map + handling the face effects. Here's the colorful one:

```rust
impl Map {
    fn render(&self) -> RgbImage {
        ImageBuffer::from_fn(self.width as u32, self.height as u32, |x, y| {
            let p = Point::new(x as isize, y as isize);
            if self.walls.contains(&p) {
                image::Rgb([127, 127, 127])
            } else if self.floors.contains(&p) {
                if let Some((index, (_, facing))) = self
                    .path_data
                    .iter()
                    .rev()
                    .enumerate()
                    .find(|(_, (pp, _))| p == *pp)
                {
                    let c = if index > 223 { 32 } else { (255 - index) as u8 };

                    match facing {
                        '^' => image::Rgb([c, 15, 15]),
                        'v' => image::Rgb([15, c, 15]),
                        '<' => image::Rgb([15, 15, c]),
                        '>' => image::Rgb([c, c, 15]),
                        _ => panic!("unknown facing char {c}"),
                    }
                } else {
                    image::Rgb([15, 15, 15])
                }
            } else {
                image::Rgb([0, 0, 0])
            }
        })
    }
}
```

The `c` value figures out how far we are from the beginning of the trail and fades down to the basic gray I'm using as a floor color (to differentiate from black empty space). 

Onward!