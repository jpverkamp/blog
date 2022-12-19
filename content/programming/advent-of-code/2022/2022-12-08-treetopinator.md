---
title: "AoC 2022 Day 8: Treetopinator"
date: 2022-12-08 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Treetop Tree House](https://adventofcode.com/2022/day/8)

## Part 1

> Given a grid of numbers, count how many of these numbers have a direct path in any cardinal direction to the edge of the grid. 

<!--more-->

Sweet. For this one, I actually started by implementing a generic `Matrix` class in my `lib.rs`:

```rust
#[derive(Debug)]
pub struct Matrix<T> {
    data: Vec<T>,
    width: usize,
    height: usize,
}

impl<T> Matrix<T>
where
    T: Clone + Default,
{
    pub fn new(width: usize, height: usize) -> Self {
        Matrix::<T> {
            data: vec![T::default(); width * height],
            width,
            height,
        }
    }

    pub fn width(&self) -> usize {
        self.width
    }

    pub fn height(&self) -> usize {
        self.height
    }

    pub fn in_bounds(&self, x: usize, y: usize) -> bool {
        x < self.width && y < self.height
    }

    pub fn index(&self, x: usize, y: usize) -> &T {
        &self.data[x * self.width + y]
    }

    pub fn index_mut(&mut self, x: usize, y: usize) -> &mut T {
        &mut self.data[x * self.width + y]
    }
}
```

I have `width` and `height`, since I want the width and height to be private to the struct. Other than that, `index` is for getting the values out while `index_mut` gives you a mutable reference so you can update. I'm ... not sure what to think about this, but I couldn't quite figure out how to pass a tuple or multiple parameters to the `Idx` type to implement `Idx`. 

Edit: Got it!

```rust
impl<T> Index<[usize; 2]> for Matrix<T> {
    type Output = T;

    fn index(&self, [x, y]: [usize; 2]) -> &Self::Output {
        &self.data[x * self.width + y]
    }
}

impl<T> IndexMut<[usize; 2]> for Matrix<T> {
    fn index_mut(&mut self, [x, y]: [usize; 2]) -> &mut Self::Output {
        &mut self.data[x * self.width + y]
    }
}
```

It's not quite the same syntax as Python, but it works:

```rust
thing[x, y]     // this does not work
thing[[x, y]]   // this does
```

But since you're explicitly indexing a 2D Matrix, I think it works. 

Anyways, let's actually work on the problem. For this, we're going to want a `Forest` (which is just a `Matrix` of heights) and an enum of `Direction`s:

```rust
#[derive(Debug)]
struct Forest {
    trees: Matrix<u8>,
}

#[derive(Copy, Clone, Debug)]
enum Direction {
    North,
    East,
    South,
    West,
}

const DIRECTIONS: [Direction; 4] = [
    Direction::North,
    Direction::East,
    Direction::South,
    Direction::West,
];
```

I wish that you could enumerate enums, but it seems that's a crate only thing for now. I wouldn't mind pulling that in, but it's easy enough to make a constant. 

Next, let's parse the `Forest` from a `Vec<String>`:

```rust
impl Forest {
    pub fn from(lines: Vec<String>) -> Forest {
        let width = lines.get(0).expect("must have at least 1 line").len();
        let height = lines.len();

        let mut trees = Matrix::<u8>::new(width, height);

        for (y, line) in lines.iter().enumerate() {
            for (x, c) in line.chars().enumerate() {
                trees[[x, y]] = c.to_string().parse::<u8>().expect("chars must be digits");
            }
        }

        Forest { trees }
    }
}
```

Straight forward enough, especially with the `trees[[x, y]]` syntax. 

Now the bulk of the algorithm, `visible_from(x, y, d)`. Given a specific point in the forest, is it `visible_from` the given direction:

```rust
impl Forest {
    // Test if the given x/y tree is visible from the given direction
    pub fn visible_from(&self, x: usize, y: usize, d: Direction) -> bool {
        use Direction::*;

        let (xd, yd) = match d {
            North => (0, -1),
            South => (0, 1),
            West => (-1, 0),
            East => (1, 0),
        };

        let height = self.trees[[x, y]];
        let mut xi = x as isize;
        let mut yi = y as isize;

        // Special case north/west edge
        if xi + xd < 0 || yi + yd < 0 {
            return true;
        }

        // Move off the current tree
        xi += xd;
        yi += yd;

        while self.trees.in_bounds(xi as usize, yi as usize) {
            if self.trees[[xi as usize, yi as usize]] >= height {
                return false;
            }

            // Deal with negative indexes
            if x == 0 && xd == -1 || y == 0 && yd == -1 {
                break;
            };

            xi += xd;
            yi += yd;
        }

        true
    }
}
```

It's a little ugly dealing with the edge conditions because we can't actually use negative number as indices. So we have to keep a few extra tricks around to make sure that we don't index `-1`. 

With that in place, we have `part1`:

```rust
fn part1(filename: &Path) -> String {
    let forest = Forest::from(read_lines(filename));

    let mut count = 0;

    for x in 0..forest.width() {
        for y in 0..forest.height() {
            if DIRECTIONS.iter().any(|d| forest.visible_from(x, y, *d)) {
                count += 1;
            }
        }
    }

    count.to_string()
}
```

Nice and short. 

In my [full code](https://github.com/jpverkamp/advent-of-code/blob/master/2022/src/bin/08-treetopinator.rs#L135), I actually have started (as of now) including a minimal amount of debug printing that I had while working on the problem. It's guarded by `cfg!(debug_assertions)` so when I'm compiling in `--release` mode, it's not included or run. That looks like this:

```rust
fn part1(filename: &Path) -> String {
    let forest = Forest::from(read_lines(filename));

    let mut count = 0;

    if cfg!(debug_assertions) {
        for d in DIRECTIONS.into_iter() {
            println!("{:?}", d);
            for y in 0..forest.height() {
                for x in 0..forest.width() {
                    print!(
                        "{}",
                        if forest.visible_from(x, y, d) {
                            '木'
                        } else {
                            '一'
                        }
                    );
                }
                println!();
            }
            println!();
        }
        println!();
    }

    for x in 0..forest.width() {
        for y in 0..forest.height() {
            if DIRECTIONS.iter().any(|d| forest.visible_from(x, y, *d)) {
                count += 1;
            }
        }
    }

    count.to_string()
}
```

It's kind of nice to make sure that my values actually make sense:

```bash
$ cargo run --bin 08-treetopinator 1 data/08-test.txt

   Compiling aoc2022 v0.1.0 (/Users/jp/Projects/advent-of-code/2022)
    Finished dev [unoptimized + debuginfo] target(s) in 0.36s
     Running `target/debug/08-treetopinator 1 data/08-test.txt`
North
木木木木木
一木木一一
木一一一一
一一一一木
一一一木一

East
一一一木木
一一木一木
木木一木木
一一一一木
一一一木木

South
一一一一一
一一一一一
木一一一一
一一木一木
木木木木木

West
木一一木一
木木一一一
木一一一一
木一木一木
木木一木一


21
took 231.958µs
```

Why yes. That is the {{<wikipedia kanji>}} for tree. :smile: I used 一 'one' mostly to contrast with it. 

## Part 2

> For each number, calculate the distance in each cardinal direction up to and including the first number equal to or larger. Multiply these numbers together. Find the largest such product. 

Unfortunately, I won't be able really use the same function again. I could probably modify part 1 to be compatible with what I need for part 2, but ... I'm not going to.

```rust
impl Forest {
    // Essentially the opposite of the above
    // Move in direction d and count how many trees are visible
    pub fn visible_count(&self, x: usize, y: usize, d: Direction) -> usize {
        use Direction::*;

        let (xd, yd) = match d {
            North => (0, -1),
            South => (0, 1),
            West => (-1, 0),
            East => (1, 0),
        };

        let height = self.trees[[x, y]];
        let mut xi = x as isize;
        let mut yi = y as isize;
        let mut count = 0;

        // Special case north/west edge
        if xi + xd < 0 || yi + yd < 0 {
            return 0;
        }

        // Move off the current tree
        xi += xd;
        yi += yd;

        while self.trees.in_bounds(xi as usize, yi as usize) {
            count += 1;

            if self.trees[[xi as usize, yi as usize]] >= height {
                break;
            }

            // Deal with negative indexes
            if x == 0 && xd == -1 || y == 0 && yd == -1 {
                break;
            };

            xi += xd;
            yi += yd;
        }

        count
    }
}
```

It's so close!

And the code for part 2:

```rust

fn part2(filename: &Path) -> String {
    let forest = Forest::from(read_lines(filename));

    let mut best_scenic_score = 0;

    for y in 0..forest.height() {
        for x in 0..forest.width() {
            let scenic_score = DIRECTIONS
                .into_iter()
                .map(|d| forest.visible_count(x, y, d))
                .product::<usize>();

            if scenic_score > best_scenic_score {
                best_scenic_score = scenic_score;
            }
        }
    }

    best_scenic_score.to_string()
}
```

With debug:

```rust
fn part2(filename: &Path) -> String {
    let forest = Forest::from(read_lines(filename));

    let mut best_scenic_score = 0;

    for y in 0..forest.height() {
        for x in 0..forest.width() {
            let scenic_score = DIRECTIONS
                .into_iter()
                .map(|d| forest.visible_count(x, y, d))
                .product::<usize>();

            if scenic_score > best_scenic_score {
                best_scenic_score = scenic_score;
            }
        }
    }

    if cfg!(debug_assertions) {
        let mut scores = Matrix::<usize>::new(forest.width(), forest.height());

        for y in 0..forest.height() {
            for x in 0..forest.width() {
                scores[[x, y]] = DIRECTIONS
                    .into_iter()
                    .map(|d| forest.visible_count(x, y, d))
                    .product::<usize>();
            }
        }

        let width = (best_scenic_score as f64).log10().ceil() as usize + 1;

        for y in 0..forest.height() {
            for x in 0..forest.width() {
                print!("{:width$}", scores[[x, y]], width = width);
            }
            println!();
        }
    }

    best_scenic_score.to_string()
}
```

I did some magic with `f64::log10` to make sure that it all prints in nice rows and columns... and get something like this:

```bash
$ ./target/debug/08-treetopinator 2 data/08.txt

      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0
      0     24      3      1      9      2      1     24      1     16      1      6      1      4     12      1      6      1      2     18      2      1   2156      3      1      2     30      2      1      9      1      2      2      4      2      1    168      1    304     42      4      1      1      1      4     18      1      1      9      6      4      2      9      1      8     15      3      1      2      3   1596      1      2      2     32      2      1      4      1     30      1      2    168      2      1      3      2      1     12   1330      4      1      8      1      4      2     56      1     32      1      1      3     96      2      1      9      2      1      0
      0      1      1     12      1     60      1      1    256      6      1      6      6      1      1      6     32      6     32      1    560      1     12      2      4      4      2      6      6      1      4     18      1      1    168      2      1    120      6      1      1    410     12      2     72     14      1     20      1      1      2      1     14     36      1     28     24      2    160      1      2      2      4      1     12      2      4      4     32      2      1     36      1      8      1      4    128      1      1      1   1440      8      1     54      6      1      1      6      2      1     36    770      1     24      4      1      6      2      0
      0     10      1      1      1      1    108      3      1      1      9      1    288      2     12      5     16      1      2     24    140     54      8      1     72      1     12      2     12      2      1      9   1344      6      1     24      4      1      2    112     27      1      2     24      1      2      1     24      2    432     27      4      2     64      1      1      1     36      6      6     48      1    432     18      1     16      1      4      1     16      3      4      2    672      9      4      1   1260      4     24      1      1      6      1      5     72      2     12      1    216      4      1     48      1      2      1      4      6      0
      0      3      3     24     12      2      4      2    144      1      2     24      3      8     18      8      1      4     32      1      6      2      2    368      5     16      4      1      2    400      6      1      1      4      4     20      1      1      6      2    640      6      1      2      8     80      8    448     24      2      2      1     32      2      3      8     16      2      6      1      6    336      2      1     96     32      4     32    480     12     16      1     72      1      4      1    288      1      2      6      2     40    384      1     24     20      7      1      1      3      1      1      3     28      1    360      2      1      0
      0      1     40      1      2      1     36      1      1    180      5      4      1     12      2      1   3840     36      1      8      1     30      1      1     96      1      1     45      2      1     60      2    128    180      1      6      8      1    240      1      1      6     54      8     48      1      2     45      1      2      3      5    320      2    160      1     12      1      2     18      1      2    576      2      4      4      1      6      1      8      1   3645      6      2      4      2      2      1     12      6      2      2    352      2      4      1     64      2     24      6     10      1     32      4      1      2    160      4      0
      0      1      6     36     36    270      1      2      6      1    120      3      2      2   7644      1      2      1    144      2      1     36      2      8      1     48      3    156      2      1      1   2046      1      4     30      1      2      8      3     15      8      1     44      1      1      1    240      2     16      2      6    180      1      4      1     16      1     36     45      1      4    162      2     48      1      4      6      1      4      3    216      2     72      3    864      1      4      6    144     10      1    918      3      1      2     96      1    180      1      2     24      4     24      1      2      9      2      1      0
      0      6      1     12      1      1      1     48     48     16      1      2    420    126      2      1     72      2      1   1764     12      1      8     27      2      1   4550      2      1      6      8     15     16      1     56      2    210     10      1      8      1     25      7      2      2      3     12      1      1   1029      7   1316      2      8     48     12      2      3      1      1     18     36      1      6     60      1    756      1      6   2436     12      1     12      1      2     12      4      3      1      1    200      1   1536      2     36      2     20      1     12      1      2    100      1     84     14      6      2     98      0
      0      1      2     48     12      3     30      3      1      1      6     16     12      2      1    840      1     18      1      1     10      1     49   1472      1     96      2      4    144      1    400      1      9      4      1    320      1     48      1      2    960    432      8      3     12      1     12     12     24      1    135      1      2     96      1      1     18    512      6   4992      1      6      2      1      6    192      1     40     24      3     16     63      2      1      6    192      2     10   2240      4      1      4     32      2      2      1   1920      6      6    648      1      1     18      1      1     18      1      6      0
      0      8     54     15      1      1      3      8    140      1     12      1      4      1      6     90      4     36    162      2      2     18      2      1   7776      2      1     18      1    120      1      4      1    144     24      1      4      6  24624      8      1      8      1      8     18     20      1   1620      3      1      6      1     90      2    189      7      2     12      2      1     36   6993    280      2      1      9     48      4      1     18      2      1    420      6    180      4      1    567      3      6      2    126      2      1      6      6      1      2   2520      4      2     12      2      1     24      1     64      2      0
      0      1      8      3      1      1     24      2      4      1    900      4      2    378      3      1      1      3      1      6   1200      3    360      8      1     36      6     80      2      2      6    120      2      1      6     16    210      1      6      1      1      3      4  10320      5      1     12      1      1   1530      6      1      6      2      1    132      1     36      1      4      2      1      2     72      4      1  10880      1      4      1      1     20      1     42      1      2    600      1    120      1      4      1     16      2     24      1    128      1      2      1    128      1     18      1      1     72      2      1      0
      0      3      1      1     36      3      4      1     48    594      1     16      1      4      1     48     36      2     16      4     16      1      4      1     24      4      1    162     60      1      8      1   2464      8      1      2      1     60      1    385     12      4      1      2    924      7     30      8      1     12      1    112     12      6      2      1    198      1    440      1     64      2      6     20      4      1      1      2  36300      8      3     36      1      4      2     18      1    120      1     40      1    748     12    132      1      4      1     40      4     72      2    308      1      1      1      8     20      4      0
      0     72      3      3    120     54      1      4      3    216      2      2    450      8      3      2      1      2      1      2      1      2     80   2208      2      1    300      2      1     18      1    372      9      1      3    720      4      1      6      3     30      8     32      2      1      4   3024      1      6      2      1     20      2     21      3    144      6      1      1     64      1    720      1      2     24      8     30      8      1   2088      4     20      3      3     24      2     36      1      4      3     10    340      1      1    108      4      2    396      1     10      3      1      1     15    168      1      4      1      0
      0      1     18      6      2      1   4680      4      2      1     12    312      2      1    588      1      1      1      8     18    120    195      3     10     12     24      1      4     18   1508      5      4      1    130    234      3      6      1      8      1     42      1      1     27      1      1      6    252      1      8    120      2      1      4     32      2      1     36    240      1     48      9      2      1   1248      1    192      5      4      1     18      1      2    390      1      1      3      2     45    260      9      1      4   3900      3      2      1      3      4     12      2    168      6     90      1      2     48      2      0
      0      8     35      1      1      3      1    294     28      1     24      1      2      8      1      2    144      2  12096      1      2      1      2      2     72      1      1      6      1      5      6   1116      5      1      6      1      1    756      1      2     12     24     14     12      3     42      1      2  33600      1      1     24     18      1      1     14     54      1      8     24      4      1     18      4      1    252      1    168      3   1508      1    320      3      1      2     36      1     24      1     32      1     60      6      1   2352     32      4      9     42      2     32      1      2      1      8   1470      1     42      0
      0      1      2     24      2     54     12      2    224      2      1      3    108      1      2    240      9      2      1      6    800      4      1      1      1   3000      3     16      2     72      8      1     90      2      8      6      4      1     16      9      1      2  11340      2      2   1890      8      1      9     45    120     24      1     24    540   3870      1      1      4      1      1      3      4    240      4     32      4      2      4     96      2      1      3  24000      1    180      6      1      8      1      4     12   1440      1     84      1     16      1      2      1     24      3      8      6     12      2     16      2      0
      0      1      2      3     16   4400      2      1      2      1     90      2      1   5616     27      1      4    384      2     24      1      6    216      2      8      1   4992      1     80      1      8      2     60      2      6      8     48      1      2  42432      2      4     30      1     12      1      1     72      1      8      1      4      1     24      1      8   9792     64      2   5616     18      3    144      3      1      2    288      1      2      1     48      2     14      2     12      2      6     10    180      4     36      1      1    108      1     24      1      8      1     54      2      2    576      6      1      1      8      1      0
      0      3      1     18    612      1      2    693     12      1      1    256      2      4      1     32      1      4    132      1      8      1      2      1     72    200      1   3094      4      1      4      1     16      1     14      1   7344    680    120      2      2      1      4    180      1      8      2   1020      4      1   3456      1     36      1      1     24      1     24      1      2      2    120      1     48      4      4      1     93     48      8      1     24     20     12      1      8      5      1      6      1      2     60     10      1      2      1      4   5610      1     16     12      1      6      1      4     12     24    272      0
      0    264      1      4      2      2     27      1      1     18      4      1    144      1      4      1   1440      1      2     24      1  13230     16      5      4      1    120      1     72     24      6      4      1    220      6  17010      8      1      8      1     20     24      1      4   1620      1    144      1     36     12      1    108    432      4      3      9     12      1   1728      2      1      2      1      2      1     35   4608     20      2      1     36      3      2      4      1      2     18   1800      1   8208      4     36      1     20    280      1     20      8      8     24      4      3     60      5    144      1      2      1      0
      0      1      3      1      1     90      1      4     24      7     60      2   1596      6      3    266      5    114     12      1   3800      1      2      2      1    100      1     24      1      2    950      1     18      1      1     12      1     12      1      4  37240      1     18      1      1    120      1    168      1      8      4      1      2   4788     60      2      1      8      1     18     38      1    152      6      4      2    640      1      1      2     16      1      1      1    320      2      1     12   4560      4      1      4     32      1      6      3   5472      1      1      6      1     60      3     76      2     20     95     18      0
      0      8      1     27     60      2      2      8      1    400   3000      1      1    108     56      1     24      2      1      6      2      6   7920     64     12      3      1      2    144      4      3     42      1     16      1      2      2      4    760    112      2      8      1    240      8      1     18      1      4     96      1      1      6      1      1     24      2    640      6      2      6     20      4    400      1      1      3   1440      1      1  16800      1      6      6      2      1      8      1     48      1   1440      2      1     72      2    480      1      4   1200      2   1920      7      1      1     12      1      8      1      0
      0      1     28      1    112      4    112      1      4      4      1   1386      4      1      9      2      3     24      1     42    800      1      4      6    168     48      9      4      6      1      1   1953    189      2      1     18      1      8     16      6      1      2    120      9      1      4      6      8      2      1      8     96      1      2      1    288     45      2      1      2      1    444      2      1    480      4     16      1      8    180      1      8      2      1   1680     16    252      4      1     27      1      2   4032     40      1      4      1     12      2      1      9     64      2     12      8     12      1      4      0
      0     16    528      2      3      2      1     50   3696      1     12    144      1      1      6      1      2     18    396   1540      3      1      1      3     25      2      1      6      1  26796      1      2      6     20      1    108      4     60      6      2      2     12      1      1      6     24      1     20      8  22638      1      1  15180      9      3      1      2      1     12    378      1      1     36      2      3      1      1      6    792      1      4     66  25168      6      1      1     32      1      4      3    432     15      2      1      6      2     72     30      4    396      2      6      6      2    120      1     12     18      0
      0      1      1   2208      1     64      6      2      1     32      1     56     72      6      1     24      1      4    864      6      1     20     24     10    120      1      2      6      8      1     36      5      4      1     10      1    600      1      1      3      4      5      2      2   1320      2     36     12      1      2     18 330786      2      1     16     24      1      2    135      1      6     18      1      6    483     69      8      2     60      1     42      1      2  14375      1     16      1     60     72      1      8      1    128      1     50      1     12      2      1    225      1      4     45      1      2     36      1      2      0
      0      2    120      1      9      1      1   2016      2      1      1      1     10    288     16      1  27648      1      2      4      1      2     24      1      8      1  34320     12      1     32      1     15     30      3    672     18      2      1      8      6      2    336      2    210      1      4      1      4  13824      6      4      1     36      1    432     10     12  20664      1      1      3      4     48      1      1     12    160      1      2      6      1     10      4     42      6      1     72      4      2     12      1      2     48      6  11424     28      1      1      6      2     40      1   2184    840      1      2     40      1      0
      0      1      4      1    288      8      1      2      1     40   1050     12      1     24      1      4      1  13600     24      1      1     28      3      2      1   6250     20      3     56      1    125      6     15      1      2      1      1     36     24      4      1    126      1      1      6      6      4      1      7      8      1     48      2     12   1134      6      1     30      2     48      5    350      1  10500      2      1     15      2     24      1      8   2250      1      1     75   1150      3      1      1     24    300      6      4      1     16   1625      2    198     50      1      2     16      1      4      3     72      1     12      0
      0     16      1      8      2      1     18     70     16      1      4      1     70      1    208   3900      6      2      1     24    125      1     24      1     48      3      1      1     12      1    180      6      4      1    144      1      1      9      1      1    420      1   4368      2    624      3     18    390     78      1     54      1      1     70     12      1      4      6     12      1     36   2886      4      1      8      1     20    126      4      1      1      1     20      2    336      1      2     18     24      3      1      1      8   1560      1     14    312      2      4      9    960      2     84      1     16      1      4      2      0
      0      1      8    168      1     88      1    140      2      1     12      1    100      6      4      1    180      4      8      1      1    252      1      1      3   1800     16      1      1      1     40      2      1     15     12      5      4     48  28728     35      1     32      1      8     40      4      1      8      1     60      2      1    560      1     10      1      1      1      4     20  32832      8      1    120      1      4      1      4    280    195      4      8      6      2      1    126    108   3402      1      4      4   2160      1      6      6      4    180      1      3     27      1      4      1     20      2      1      4      1      0
      0      6      1      2    168      1    672      1      4      3    144      6      8     48      1    960      3      1      1      8      6      1      2    224   4704      1      2      3      2     60      1    224     12      2      1      3      2      1      2     72     12      1   4200      2     32      1     12      1      1      3      1     21     10    112     36      3   2016      4     80      1     12      1  48384      1      8     96      8      1     10      1      3      1      1     80     48      1      1      3      2      6      1      2    480      1     10     30      1  20020      1     20      2    504      1      8   1680      6     32     63      0
      0      1      4      2      2    145      2      4   1078     12      1      1      3      1      2     21      2      1     72    798      1      2   1914    319     10      2      6      1      1    210      8      1   5568    290      1      4    288      4    400      6      1      1      9      1      2    294      1      2    120     14     36   4437    261      1      2  18705      3      1      1  13572      3      1      1     32      1     12      1      6     24      2      4      1     64      1     96     12      8      1   2320      1    288     20      2      1      2      1     10     10      1     36      1      2     12     40      4      1      6      1      0
      0      1    504      9      1    115      3      1      8   1080      4    224      1  18720     28      2     36      1      4      6      1  20160      1     24      1    120      5   1680      1      4      1  12090     10      1    160      1     24      1     12      1      1      9     24      2   6600      4      1      1      3   7350      1     24      2      1      4      1      2     30   3780     10      3      1      1      3    105   1470    240    180      2      1  17640      1      2     30      4      2      2      1     15   1140      2      1     16      3      1      6    378      1   8400      1     32      3      1      1     96      4      1      4      0
      0    775      4      1     12      1     36    336      1      1      3      8      2      1      2      1     81      8      1     38     60      1      4      1   1680      1     24      1      2   5394      2     20      1     16      1    620      1    372      1    124     31  43214      1    248     40    186      1     20      2   1470      4      1      2     24      1     72      1     84      2      1    144     10      3   1440      2      2      6      1     36      2      1   6696      1     12      4      1     48     18      1      2  15624     24      6     75      2      2      2     12      1     12     20     18      2    280      1    186      1      2      0
      0     16      1      4      3    300      1      4      4      4    480      1   3456     16      2    336      1     28      2  23712      1      3     54      1     10     54      1      4   8960      1   1280      1      4      1    128      1      8      1     24      1    360      1      8      9      1      4    576  60160      1      1     18     24    138     60      4      2      8      1     40      6      1     72     48      1      1     60      1     24      1    128      2    324      3      2      1      6     30      1      4    570      3      3      1     60      1      6      1      1     20     12      1      3      2      1      3     18      8      2      0
      0      1      3      9      8      1     12    112      1      4      1    288      6      1      1      9      2   2040      8      2     12      1    880     27      2      1     12      1     12      2     24      1     12   1650      2      4      1      8     40     18      4      1    225      1      1      1      1      5     48      4      1      2    260      1      6      1      1  67650      3      4      4     48      1      2     18      1     20     60      1      8      6      4     22   3300     24      1      1    144    420      1     24      1      4      2     64    182     36      4      1      2      2      1     84      2     90     36      2      1      0
      0      2      1   9282      1      6      1      1    480      4      2      1      1      8      4      1    208      1      1      1   1260      1      2      1      3     20      1     56      1    435     14      1      1     12      1      4      2    168      1      4      1    192      1      8      1   9180      1     12      1      2    408     48     21      1     12   3225     18      1      2     75      1      3      4      9   1700      2      1     18      3    140      2      1      6    300      1      1    108      1      2     36      1      1  35904      2      1     72      1     70      2   1224      1    300      9      2      1     18    340      2      0
      0      1     30     18   6720      2      1     12      1     10     18      1    648      1     40      1      4      2    288      2      1      3     24      2      1    125  14560      2      2     12     16      4    216      5      4      1      4      1     60      1     12      4      2    344      1     16     21      1     20      1      2      1      2    840    210      1  23520     48      2      1   1176      1      1      1      4      2      1      1      4      1      8      1      1      1  23520      6      2     60      2      1      4      3      5      6      2     48      1      1     15    108     32      3      1      2     16      4     12    105      0
      0     25      1      1      1      8     25      4      1    216      2      3      3   1638      1     24    180      3      4      1      1      1      8     12      1  16200      1      1     24      1      2    600      1      4      4    280      1      8      9     81      4      1   9072      6     15      6    288     12   3600     15      4      2     24      1      4      3      4      2     64      1      4      1     64      1    136      1      4      3      2      1     36      1     84      2      1   3105      2      1      6      8     12      1     14     15      1     10    144      6      1      2      1     30      1      4     64      1      1      1      0
      0      5      2      4     16      1    648      1     18    666      1   1776      1      1    126      1      4   1887      4      1    555     14      1     18      5      5      4     35    280      4     48      4      8      1    592      3  47952      1      2     12      1      4     12      4      1     12      1      4     48     78      1     12      1      4      2      1     30      1      4      1     16     20   2886     12  10064    175      1      6     12      3    315      5      1      9    144      1     36      8      1    285      1     24      1     48      8      1     18      2      4    648     16      1    780      1      4      1     32      2      0
      0      4     18      6      1    192      1    196      2    108     12      3    180      4      1      4      1    255      1     12     15     24     40      2     28      3      1      1    560      1      8      1     24     20      1      1      6   4218     16      1   4104     56      1      1     12      1      1      1     21      9    342     16      6      6     48      1      4      3    912      8      1   3420      2      1      4      1     80  63612    228      8      2    216      1     50      5      1      1      1      2      6     14   1938     24      1      2      1     32      1      6      1      1     36      1      4    504      1      1    135      0
      0      8      1      8      1      2     30      1      1     45      1      2      6      4   2730     84      6      2     84      6      1      4      1      2      1     75     60      1      1    120      1      1      1      4      6      1      1    444      1     16      1      2     10     18     48     36      3      4      2     80      3      1      1      8      1    860      1      4      3    100      4      1      3      4    180     24      1      1      2      1      2     60      4     27      4      3   5148      4     12    114      1     20      3     12      8      1   1080      6      2    108     12      1      1    144      1      5     24      2      0
      0     45      4      1      6      2     45     56     11      2  25200      1      2      1     24      2      6      1      1     72      4      4      1    253  13440     30      4      6      4      1    120      1      4   3960     14      3     63      1      1      1     16      2      1    126      1      4    300      1      1      6      1     20      1     60      4      1     18      1     40      6      1     18    480      1      4      1  66560      1     32      6     36      8      1     12    216      1      4      1    168      1     72      1      1      3      1      4     12      1    400      3      1      1     18      1     20     54      1      1      0
      0      1      4     21    144      1      4      1     64      1     10    220     12      2      8      1     50      6  17712      6      1    144      3      6      1      4     12      1      6    464      2     20  22304      6      1     20     18    132      1      4      1     28      2      1     32      1      4      2    528      1      6      6     21      2      1    144      2      2    252      1     24      2      1     50   7344      2     18     12      2    126      5      2      2      6      1    492    352     32      2      8     17     54      1   7380     34     10     24    143      1      4     60      5      1    270      1      2     36     15      0
      0      1      1     36      1     48      1      2      6    288      1     10    320      1      2     18      1      6      1      4     32      5     88      3     42      1      1   6804      1      2      1      2      1     18     20      1     12      1      8      2    960      1    180      8      1     54      1    200      1      4      6      1     30      1    192      1      1      3      2      1   2268      1      8   6300      1   1008      3      1      1  34104     56      1      2     12      1     45      1      1      1      1     60      1      6      8  21168      1      6     60      4      6      1      2   1260      1     16      1      8      1      0
      0     18      2      1      6      1   1512     12      2      1      8      4      1   1456      3      8   6880    135      1      1    210      1     18      1      8     18      2     81    210      2      2     84      1   1188      1     28      8      1     12      1      1     12      1      2     96      1      2      9      2      1      3    540      1      2      1     24    160     60     12    688      2    180      1      2    252      1     12      1      4     18  10836      2   2064      1     66      8      4   1806      3     38      1      2     42      2      1     36      1      2      1    144      6      1     18      2      1     18     96      1      0
      0      1     28     96      1      8      1    192     10      8      1     24      4      1    630  72600      2      1     18     48      3      6      1     24      1      2   2600      1      1      3    192      1      6    462      1      2      6      9      1      4     18      2      1     24      1      8      1    112      3   1050      6      1      1     36      1      1     15      8      1      1      1      5     12      2      1      6     24      1     16      1    588     36      1    224      1      4      1      4   1760     24      2      1      6      1     10  24024      1      8    882      2      1    660      6     60      6      1      2     18      0
      0      4    900      1      2    168      1      1      3      4      2      1     60     12     25      1      6      1      1    988      4      1      6    168      1     12      1      4      6   1740      2      1     27    198      2      8      1      4     27    540     36      1     12      1    144      9     10      1     64      1      1      1    288      1      6      1      6      1      1     12    192     32      1     12      6    576      3     28    540      2     56      4      2      8      1    140      8    420      1      2      1      2   3520     24      1      3      6      1      6    108      2      1    198      1     28    216      4      1      0
      0      1     84      1     30      1      6     12      1    864     25      1      3      1      1    288      1     12     45    114      1      1     54      4      1   1800      2    144      2      2      4      3      4   3630      1      2     12      1      2      1      1      1      6    180      1      4      3     16      2      1      4     24      1     12     24      3      1    468      1      1      1      8      2     12      1     48      1      2      6      1   1092      1     36      1      2      1      2      1    960      1      4     15      8      1    336      8      5     96      1      4   7728     42      1      6      1      1     20     20      0
      0      4      2      1    216      4      1   3948      3      6    105     50      1     12      1      2    160      1      4      1     96      5      4      1     40      1    104      1     40      1      4      8      1     99      7   1645     12     72      1     48      1      1     30      3      8      1     24      1     32      1     18      8      1      6      1      2    360      2      4     96      4      1     30      2      2      8      1    288     60      4      1    243      2     18     28     24      4      1     30      9      1      4      6     30    112      1    432      1      8      1      8      1      1      9    608      6      1      2      0
      0      1      8   1152      2      5     15     12      1      4      1     16      4      1      6    192      1    510      1    114      1     14  63360      4      1     48      1     16      1     24      1      4      8      2     12    315      1      3    864      1     18    102      1      8      1     36      1     48      6      1      6      2      6      1     20      1      3      1      2     45      2     10      2      1     12      1     40      1     81      1      4   7776      2      1      2      1     10      3      2    640     36      1      2     60      1     48      1      8      9   1728     15      4      2     60      1     54      2      1      0
      0     45      1      8      1      2    216      1   9408      1      1     60      1      1      3     12     20      1   1008      2      2    240      1      6     42      1   3120      1      4      1     32      1      2      1   3332      2     72      1      8      2      1      2    504      1     12      1      1     12      1     70      4      1      4      8      1    256      4      3     12      8      1    320      1      8      1     20     10      8      2    112    168      5      6      2      1     12    320      4    240      2      1      6     16     30      1     24      6      1      1      6      1   3360      1     50      8      1      1      2      0
      0    750      8      1     90      2      1      2      1    252      1      1      6      3    150      1     21      2      1     95    224      4      2      2     24      8      1    432      1     30   1500    450      8     42    351      1      8      2      2      9      2      1     12    198      6      1      1      1      1      1      6      4      1      6    396      6      1     24      1     18      6      1    300      1    252      5      1      1      1      1      6    756      7     12     36      2      1     20      3      8      2    216     32      1      6      1     12    792      1     36      4      1    540      1     28      1     40     12      0
      0      1      1      9      1      2     12    112      4      4      4     56      6    240      1      1      6      6      4     20      2      1      6      1     10      1    208      1     24      1    600      2      1      6      2     90      1      6     27     12      6      6      1      2     30     36     80      2      8     10     16      4     20      1      1      1      1    100     12      2      1      6     16      6      1      1     16    240      9     12    168      1      6    525      1     24      2      2    800      1     24      1      2     20      3    364      2      1    630      1     30      1      4      1      2    378      1      4      0
      0      1     72      8      8      1     18      1      1     54     30      1    100      1      4     48      1   6426      1      4      1      2      5   7176      2     60     18     16      1      8      1     40      1      1      1      1    540      1      4      1      2     30      4     56      1     28      1     16     33      8      1     39      5      1      1      1      1     10      1     16      6      1      1     24   1638      1      4      1      8      1     12  17388      3      1      1   1288      6      1      2      6      1      1     42     45      1      2    432     10     20      3      1      6     72      3      8      3      1      1      0
      0      3      4      1     24     23      4   3150     16      1      2      1     80      4    252      1  43200      1      4     36      6      1  34650      1      2      4      1      4      1 138330      2     24      3      8      4     32     45     18      2      1    168      6      1      1      3      1      1    112      1      1     30      4      4     16      3     32      4      8      4     18     48      4      2     18      6      1   7488     36      1      8      1      4      2     24      1      2  35640      2      2     90      4     24      1      8      1    312      2      1      2     36  12600      2      1      4      1      8      1    840      0
      0      2      1      8      5    100      1      2      3     16     40     12      2      1      4    900      5     16      2      1      2    180      6      1   2016      6      4    288      6      1      1   8184     90      1      1      1      1     24     12     36      2      1      8     10     12      1     12      1     24      1      1    288      1      1      2      1      1    216      1      4     42    490      1     10      1    192      1      1    168      9   7392     12      6      1    165    184      1      2      9    114      1      1      6      1     15      3      2      1     90      2     12      1      8    150      2    180      4     10      0
      0    215    774      1      1      1      2     40     48      1    600      1      4      2     20   2580      4      2      1   3440      2      4      1   1449      6      4      2      1      2      4  46440      3      1      4     45      4      2      3      3    198      1     42    240      1      1      6      4     10      1      1      1      1    240      8      1     12      1      1    840      1      3      7    720      2      1      6      1    100      1      6      1      1    300      1      1      6     40    100   3440      1      8      6     84      6    344   1118      3      6    330      1      2    360      1     12      4      1    840      1      0
      0      2      1    432      1      4      9      1      2    192      4      1      2    260      1     12      1      8    378      1      2     12      1      2  10080      1     16      4      2     90      2      1     16      1      4      1    208      2      4      1      8      1      4      2   5500      1      4      1      4    125      1      8      3      2    150     16      1      6      3     36      1      1     48      1      6      2    384      1      2      2      2     10      1   5250      4      1      3      4    120     16      1     33      3      1      1     32      1      1      1     24     32      1  30492      1      1     18      2      2      0
      0      2      1      2      8      5     96      1    320      3      1      3     12     80      1      1      1      8    378     16      2      9      8      2      1  15375      1      6    630      1      2     12      1    726      1    320      1      1      1      8    560      1      8      1      6      4      1    224      1     32      1      4      1     72      2      2    360      4      1    126      1      1      1      1     20      4     28    492      1    348     12      4     45      1      1     12      1    630     10      1     32      1      6    360     28      2      2    165     30      2      1     16      1     20     42      9      1      4      0
      0     12     15      2      1   2400      2      3     16     36      2    630      1      2      9      4      1      2     14      1   2400      4      1   8280      3      1    144      1      1     12    640      1  21760     12      3     14      2     48    416      5      1    108      1      2     18      1      8      1     24      1     10   1768      1      4      1     16      3      1      1     24      6      1     48      2      1      9     24      2    136   1160      3      1     48      2      8    552      1      6      1      8    510   1360      2      1      6      2    144      2      2     72      1      1      2      1     25      2    168      1      0
      0      2      1      9     36      3      8    270      1      4    200      1      2     12      1    180     40   1190     32      2      3      1    300      1      1    126      2      1     54      1      1   2418     24      1     12      1      2      1      4      3     24      1    672    294      1     56      8      1      2      1   8064      1      6      1     24      2      1     12      8      1    550      1      2     10      8      1      4      1      6      2      1    132      1      2     45     69      4      4      8      1      2      8      2    960      6     12     12     32      1      1      1     64      3    100      1      4      1     40      0
      0      2      1     30      2      1      4      1   1216      1    304      8      1      3    392      6      5      6      1      4      1    315      1      1      1      1   1248    108      4      1      8      1      1      6     24      8      2     18      1      1      9      1      1     12      4      1      2     36      1      1      6    204      1     24      1     48      1      1     60     18      2      1     96      3      1      1      4      2  13680     64      1     10      1     48      1      1    200  19152      1    228      2     16     24      1     20      2    192      5      6     54      8      1     12      2      4     72      2      1      0
      0      4      1      3      4      1     36      4      1    162      2      1    120     96      3      1      1   5032      2     16      2      8      4    108      6      2     42      4      1      1      3      4      1    792      6      3      1     72      6      1   1776      1      8      3    200      4     60    296      6    144      1     24      2      1    120      1    144      8    296      2      4      1     32      2     36     32   4736     24     14      1     56    162      1      2      1     16      1     24      2     38      1      1      3     64      8      1     12      4      1     24      3  24864      5     80      1      2      3     64      0
      0      1      1     12     30      3     32      2      2      2     16      2      4      1    280      1      1     12      4    100      3     63      1     10    504      1      1      3   5040    216      4     18     24      1      4      1     16      1     18      3     10  18081      1      1     24      1     10      3      1      1     81      1     42     12      1    516      1      1      2      2      1    126      7     90      1     18      4      1     72      1      1      4      8     12    972   2484      1      5    162      6      2     16   1008      2      2    858      2      1    252      2      1      3    144      2      2      6   2016      1      0
      0     48      5      1      9      8      1     72      1   1260      1    140      1     60      1      2      1      1     56      5    300      5     36      6      1     36  19110      6      1      1     12      1      2   2310   1365      1      8     30     12      5      8      1    360      4      1    216      1      2     66      2      6      4      1     90      4      1      8      8      1    360      4      1     12      1     10   2310      1     16      1      6     20      1      1      3      1    280      6      1      2      1     15      1      2  16800      1      1     27      2      1     12      1     12     12      1     36      2      1     12      0
      0      1     90    612      6      2     60      4      2      2     16      5     12      1    224      1      2      2  12852      6      1     27      2      1    150      1      4      1      4     20     36      2     16      1    510      8      2    333      1     12      2      1      5      6      2      2    108      5     16      1    168      4      4      1      2     40      1      2      8      1    100      1      2      2  16184      5     18      1      8    200      1    324      4      1     90      3      4      2      2     50    540      2      4      3      2      2    288      1      2    432      8    136      1      4      6   2720      2      4      0
      0     20      8      1      1      1      8      1    105      1      1    308      1      4      6      2     20      1     21      1      4    630      1      4      1      2    700      6      1      1      9      4      1     56      2  18480      1     24      8      1      4      1     20     72      1     72      2      1      6     64      1   2376      3      6     72     36      2     16      1    792      2      9  14256      1     12      1      2     12      1      2   3360      2      1     36      4      1      8      2     10     12      1      1    576     66     60      6      1     40      1     90     16      1      4      4      1     10      2      1      0
      0     64      1     60      4      2     36      6      1     72     10      2    120      3     48     14      7      5     72      1    300      4      6      6      1     70      1  20736     44     96     28      1     12      2      1     24      2      2    304     44      1     16      1     16     10      1   1408      6      1      1     32      5      8      3      1      1     20   5412     60      1      8      1      4      1     16      3    300      1      4      6      1    320   7488      1      2      1      4      1     24      1      1     24   5120      1      1      9      4      1    660      1      8      2      2      1   1368      1      6      6      0
      0      7      6      4   1240      4    310     16      1      1      9    682      3    558      1      2    192      3      1      3   1860      4      1     72      6     16     16     40      1      4      1     10     10      6     12      1     24   2294     31    155     20      1      8      2     40      8      1      8      1     24      1      1  14880      1      2      2      4    930      1     16      3      1      1 162750      1      1      3   2232      6      1      8      1      4      1    162      3      4  11718      1      2      1      2      1     12    168     20      1     16    124    558     28      1      4      8      3    100      1    217      0
      0      1      4      1      4      6      1      2    768      8      1     30      6      1      4   2025      1      4     12     20     50      1     12      2      1     45      6      1      6    348      2     72      1      4      1     48      1      1      6      8     12      6      1      1   1320    270      2      1   1800      2      4      6      6    150      9     60      8      1      8      1   2100  15540     42      5     16      1     12      6  25200      1     72      4     16      1      2      2    240      1      4      9      4  25500     56     18      1      2     64    396      1    198      1    100      1      1      1      1     20      2      0
      0      4     20      4     32      1      1     30     12      1      1      1      8    260    336      1     20      2      1      3      1     10    440     58    105      6      1      8      8   3364      1      2     12    696     10      1   1885      8      2      1      2   8323   9744     12      2      1      2    420      1      1     21      1      1      3     24      1      2     98      1     20      1      3      1      1      7    696      1      1      1    580      1      1      3    624      2      1      9      1      2    435   2610     17      3      2      1    120      1      6      1      1    560      1    192      1      1     18     24      1      0
      0      1     48      1     20      4      3      2      1    216      3     16   4032      4      1      6     64     42      1      2    224      2      1     32      1      6      1      1     10      1      2      8      2      2     34    420      4      1    252      6      2      4     15  28896      4      2     12      3      2   1512    840      1     12      2      1    280  10584     21      2      1      1     72     12      1    588      8      2     54      4     56   3920      2     16      1     24    196     22      9     10      1     22      9      8      2     54      2      4     66      6      1     32      4      1      6    224      1     20      6      0
      0     16      1    120      2      1      4     96      1      2     30      1    252      1      4    810      2      2      9      4      1   3402    162      1      4     48      6    864     24      1     20     60  20736      1    324      4      1    648      2      2     27      1      1     24      1      8      2      2      1    135      1     30      9   4293   7128      8     15      2      1   2496     36      1      1      1      4      1     72      1      2      1     24      2      1      8      1      1     68      1   9720     48      2      1      1     24      2      1      7   2376     10      6      1      2     12    600      4      6      1      1      0
      0      1     16      1      8    420      1      4     64     60      1      2     18      2     75      1      2     30      1   3990      6      1      6     10  22464      1      4      1     20     60      1      2      2     24      2      1    756      1      2    117      4      6      2      1    128      9      1      1     72      2      1      2   1248      1      6      6      1      4   7488      1      3      1      1     60      1      2   1536      2    128      2     12      3   1248      1   2496     54      2      1     80      2      1      6     48      1    936      3   2496      3      2      1     48      1      2      1   1664     10      2     20      0
      0      4      1     42     18      7    108      1      1     48      6      1      2     64  15400      2     24      6      1      8      1      5      1      2      8    400      2      8      1     16    140      4      1      2     48      9      1      4     12      1     40     24     12      2     18      2     18      6      2      4    270      1      6      4      1    500      1   1350      1      8      2     36     10     30      2      1    225   2325      1     96      4      2      4     48      1      1    132     36      1      4     72   1200      1      8      1   1144      1     24    150     12      1     54     52     50      1     54     12      1      0
      0      7     48      1      2      1      4   2520    336      1     30      8      1      8      1     45    576      1     36      1      1     27    576      1    140      1      6      2      1   2784      2      6      3    960      4  16800      4      1     48      1    480      3      1      1    432      1      1     12      1      4      2     24      1     12      1     72      6      8      2     14      8      1      1      1     64      8    147     24      8      4      2      1      2    504      4      2   1584      2      1    171      1      2      6    480      1      1     12      2     16      2     48      1      2    100     36      6      1     32      0
      0     10      1      8     16      2     10      1      4      2   2250      3     54      1      4   1035      6      1    378      2     30      1      2     36      1   1150   1380    140      1      4      1      2    720      1      2      6      1     40      2   5382      1      4    690     16      1     45      2      1    420      1      1      1     24   2760      9      1      1      3     15   1656      1      2  17388     64      6      1      2     18      1      4    189   1944      2      2      3     72      3      4      1     84      6     52    252      1     30   1794      5      1      1      1      4    420      1      2      4      2    200      1      0
      0      5      1      1      1      1    648      2      2      9      1      1      3      2      3      1      2      9     12     76      8      1    100      1      3      3      1     10      1      2    120   2790      3      1      2      8      6     72      1     88      2   2706      1      2    396      1      6    924      1     20     36     10      1      1     30      1    144      6      1     22  26752     36      1      4      1     16     10      4      1      2      3   6534      2      1      6      1     88   1386     20      2      1      4      1    216      1      2     96      4      1      9    168      3     30    660      2      1      6     16      0
      0     26     54     18      2      2      6      1     24    144      2      2      3     16     12      2      1   5712     20      4      3    120      2    150      1      6     12      2  45276     81      2      2     72      1      2    147      4      1     12      1      2      6    588      2      8      3  21252      1    504      1      2      3     16      1   1512      9   1764      1     12      1    252      1      2     36      4      1   1134      1      6    348      1     42      5     18     24      1    264      1      8      8      1      1      3     20     12      4      1    132      3      2      8      1     12      1     12      6      1      2      0
      0      4      1      2      1     40      1      8      1   1080      3    200     84      1      1      9     72      1     16      1      4      1      2     15      1      2    312      1      2      3  15000      1      2     12      4     90      1     48      4      2     12     96      1      2      5      4      1      8      1   1960     40  12220      1      1      9      2      2     42      4      1      2      1      2      1     56      4      1    320     12   1160      1      2     36      2    288     36     12      1      1    336     18      2     24      4      2      1    560      1     40      1    640      1      1      2      1     30      1     84      0
      0      9      1      2    144      1    144      1     40      1     30      2      2   1140      2     16      2     12    684    532      1      1     12   1216      6      2      1     48      1      8      1   5301      4      4    108      1    140      1      1     27     12    190      1     32     16      1    836      1     24      1      2      2      4     16     48      1      1   2508      1      6      1     96      8   1120      1      4     24      1      1     39     15      4     25      1      6      1      2     75      1      1      1     48  15808      1      4     24      2    330      1    924      2     12      1     36      2      1    280      1      0
      0      2      6    378      1     56      1    144      1     24   1620      8      1      2      3     16      2      1      9     36     60     24      1      1      1     25      4      1     12      1      2     93      1      2      6      1     12      4     16      1      1      1     54      4      1   1125      1      8      1      4   1440      1      2      1      4      3      6      7    432      2    192      1      4      1   3240      1      1      6   4320     29      2      4      1     18     12      4      2    105      1      1      1      4     10      2     60      1      2     54    360      1      2      1     24      1    576      2      1      3      0
      0      1     12      1     16      1      2      1    256      1      2      4      2      4      2     14      6      2      2      6      1      1    220      2   5712     17     90      1      6      6      2      5   9792      4      1      9     18      1      1      1     16      1     24      1      8     36      6      2      1     24      5      6      8      4    168      4      1     21      6      1      1    952     12      2      1   1632      2   1054      2    102      1     16      1      4      3    180      1      4     24      3  16830      1    160      1      4      1      8      6      1     16      6      4      1    120      1     12      1     12      0
      0      6    768      1     18    640      3      8     21     40     10      1   3840      1      2      1     40    375      1      1      3     24      5      6      2      1      2    756      4      1      2     64      2      1   1632     16     16     96     16     12    160     24      1      6      1     15      9      6     30      2      2     32     64      1      4      1  13440      1      1     60      1    240      2      1    198      1     48      1      1      3      4      1     12      1     32    704      8      1    300   8512      2     48      2    384     28      1      2      6     18      2      2    210      4     12      1    144      3     32      0
      0      2      1    135     30      1     40      6      1      2      4     10      6      6      1   4500      4      3     12      3     60      1     60      1      4      2      2   1215      1      4    450      9     12     10      1      4      3      1   2850      1      4      1     20    300      8      8      1     20      1    360      1      1      1     16      5    162      1     12     72      6      1      1    480   2100      2      6     72     12     10      1      1     36      4   1500      1      2    432     36      1      2      1      4      1     18    448      8     24      1      4      4      1      8      1     28      1      8      4      2      0
      0     10      1      1      1      4     30      1      4     18      4     30      2      1     36      1      1      3     90    224      1      8      1     40      4      1   2184      1    980      6      6      6      1      5     20      1      4     24      1     30   8960      1      2      1     16      1      1      1   1344      2      4      2     32    126    252    602      1      1     30      1     96      1      1     12      3      2      2     15     40      1    144      1     48      1    576    138      8      2      1      1    288      4      8      2     12      1    264     24      1      1   1344      1      8      1   1344      1    280     14      0
      0      1     24      4      8      2    702      1      8      1      4      1     72      1      1    162      4      1    468      1    312      9      4      1      3     11    252      2      1      8      1      2      1    858      1    162      1      4     12      1      1      9     32      1   1144    338     12      1     54      1      1      6      1     30     96      1      3      2  13520     12      1      2     32      1    108      1    112      8      1     24      2      1      1   5850      5      8      2      1      2    285     10      1      3      1      1    432      3      2    117     24      2      6      1    180      2      4      2      2      0
      0      2     20      1      4      1      2     90      1      1      6    264      1     18      6      4      1     72      1      6     33      1      3      6    960      4      2      9      2  15660      4      1      6      2    480      1      4      1    240      2      2     48      1    540     10      1      1     18      1     54     90      2      8      3      8     60     48     42      1      4      1     48      1      1     28     18      1      1   1152      1      1      9    192      1   1152      1    216      3     12     36      1      8   2880     54      1      8      1      1      3    252      1      2    351      2      1    432      8      1      0
      0      1      2    216     22      2      6    182      2    110     80      1      8      2     24      1   1584    220     66      1      2    320     48     10      1      1      1      1     12     88      4     12     16      1      2      1     40      2      4  21879     12      1     18      4      1      6     18      2      1     36      2      1      4      1      5      6    374      1     32     10      1     40     48      3    136      1     16      1      6     10      2     84      2      4      2     72      1    294      1      2      6      4     14      1   4312      8      1      4      6     24      6   2695      1      4      9      1      1      9      0
      0      4    160      2      1      2      8    280      2      1      2     24      2      1      6    180      1     24      3      2     18   2520      2      1     60      2     12      4      1     40      1      2      1    120     18   2100      1    600      1      1      1      8    250      2      4      4      1     25     36      1      1      6    800      1      4      4     10   1050      1      2    720      6      1     30     12    350      1      1      1     16   6720      2      1      9      1      2      6      4      2      8      4  24310      1      1     12      2      4    216     27      1      2     60      1    900      4      8      1      2      0
      0      1      1     24      1     14      1      2   1728      2      4     27     12     90      2      1     72      1      2     60      1      1      1   5175      2      1     24      9    200      1     24      2  15552      2      2      3     72      1      4     24      2   1080      1      1      9      1      4     12      1     12    108     18      3     16    128      1      7      1     24    182      1      4     12      1      2      2     42   1674      1      2      1      1     30      2    180      1     24      1      6      1   7776      4      1    252      3     16     10     90      1     16      2      1    810      1      2      1     12      1      0
      0    416      1      4      1     32     42      1      1     54      1      1      6      4   1120     24      3      1      2     10      1     24      5      1   3744     60      2      1      4      4      4      1      8      1      4     12      3     26   2432      5     24      1     12      2      2    240      3    240      1     12      1      4      1      4      1     24      1     70      1      1      4      1    360     16     32      1    512      1      6      2     16    120      3      1      2    144      1     12      1    152      1      2     36      4      2    624      1     42      2      1    216      4      1     18      1      4     24      3      0
      0      1     42      8      4     50      2     24      2      1    560      2     56      1     28      1     16      1     16    147      3      3      1      2     12      2  12012      1     12      1      2     36      1      6      9      1      4     33      4      1    280     14     14      4     24      1     36      2      6     70      6      1      1     48    350      1      1      1      1   2730      3    280      3      1      2      6     30      2    200      1      2      9    140     24      2      1      2     70      9    266      1    340      1      1      1      4      4      1     72      2      4      1     56      9      2      4     42      1      0
      0     28      1      1     54      1      1      3     42    144      1     72      1      4      1      8      1    432      2      1      3    336      1     36      1      1     18   4374      1      4     18     27    144      4     30      4      1      4      1     15     72      2      3   1548     12      8     24      1     14     12      1      4     36      2      1    756      4      1   2160      1      4      1      6      4      1      6      1    324      1   1188      4      1     24      1     24      6     24      6  10800      4      2      4      2     12   1260      4     36      4      1      4      1     20      2      1     32      3      1      1      0
      0      1      2     36      1     40      4     30      1      1     60      1    480      2      1      9    640      1      8      2     24      3      2      1   1440      8      1      2    400      5      3      2      3    125      8      1     96      2    400      3      1      1     12      1      6      7      5      6  12000      2     96      2      1    350      6      1      1     24      1      1    700      2     12      1    216      3      2     12      2      1   4200      6      1      8      1      2      1     12      1     16      1      2      3     24      4      1      6      1      4    648      2      1     12      1      4      4      6      9      0
      0      8      4     48      1      1      1     16      8      8      1     32      1   1560      1      6      2      2     12    216      1      8      1    128      6      1      4     32      2      1    720      1      1     24      2     32      1    288      2      1     18      8      1    960      8      6      1      1     33      1      1      1     12      1      1     24      4      1      1    132      1     12      1    960      4      1     72      1      2      9      2     30      2     24   3840      1      2     12      8      1     40      4   1792      5      1      2      6      2    300      1     24     16      1    150      2      1      4      2      0
      0      2      1     18      1     24      2     35      6      1     12      1     45      4      1     42      1      4      6      1      8      1   1056      2      1     30      1      6     54     12      1   2232      1      6      1      1     18      1      1    144     48      1     40      4      2      1      8     10    192      2      4      6    252      1      4    198      1     16      1      4      1     90      1      2      2      1   1056      2     24      1      1     36     27      2      1    240      1      2      1    240      1      1      1     12     90      3    792     10      1    108      1      1      6      1      6    162      1      1      0
      0     20      1      1      1      4     30     28      1    112      2      8      1      1     30      4    168      1      2      6     12    168      2      2     12    176     48      4      1      6      1      1     36   1584      2    144      1      8      2      8      1     30      3      4      2     96      1    408      1     24      1      4      6      9      2      1    126      1      1      6     12      1     24      1    408      3      4      1   1200      2     20      4      1      6      1     10    128      2     48      1      8     15     32      2      4    192      1     10      1      2      1      1     10     64      2     12      6      3      0
      0      1      1     12      1      2    378      2      1      4      1     20      1      8      1     72      1      8      1     57     22      1     24      1      4      1      1      1     16      1      6      6      1      2   1224      1     16      1     32      1      4      6     18      1      1     15      4      2      1      4    160      1      2      3     24      8      1     28      5    936      1      4      1     24      1      4      1     16      1     10     44      1      4      1     60      3      2      1      3     20      1     11     16      1      4      1      8     77      1      2     63      4      1      1      1      8      1      7      0
      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0
330786
took 22.120166ms
```

Yeah... that's very large. :smile: 

It was useful on the test data though:

```bash
$ ./target/debug/08-treetopinator 2 data/08-test.txt

 0 0 0 0 0
 0 1 4 1 0
 0 6 1 2 0
 0 1 8 3 0
 0 0 0 0 0
8
took 376.625µs
```

## Performance

Still too fast to optimize much:

```bash
$ ./target/release/08-treetopinator 1 data/08.txt

1814
took 438.458µs

$ ./target/release/08-treetopinator 2 data/08.txt

330786
took 1.566ms
```

Coolio. 