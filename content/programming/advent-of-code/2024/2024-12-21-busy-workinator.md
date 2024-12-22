---
title: "AoC 2024 Day 21: Busy Workinator"
date: 2024-12-21 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2024
programming/topics:
- Recursion
- Memoization
- Tracing
---
## Source: [Day 21: Keypad Conundrum](https://adventofcode.com/2024/day/21)

[Full solution](https://github.com/jpverkamp/advent-of-code/blob/master/2024/src/day21.rs) for today (spoilers!).

{{<toc>}}

## Part 1

> You are trying to type a code on a keypad:
>
> ```text
> +---+---+---+
> | 7 | 8 | 9 |
> +---+---+---+
> | 4 | 5 | 6 |
> +---+---+---+
> | 1 | 2 | 3 |
> +---+---+---+
>     | 0 | A |
>     +---+---+
> ```
>
> But you cannot type directly. Instead, you can control a pointer on the keypad with arrow keys:
>
> ```text
>     +---+---+
>     | ^ | A |
> +---+---+---+
> | < | v | > |
> +---+---+---+
> ```
>
> Whenever you type a `^` on the arrow keys, the pointer on the keypad will move up one, etc. When you type `A`, then the pointer on the keypad will type whatever it is pointing at. 
>
> But that's not enough either. Add a second keypad. And then a third, that is the one you are actually controlling. 
>
> For each output sequence multiple the length of the minimum input sequence needed to generate it by the numeric value of the input sequence (ignoring any `A`); sum these. 
>
> Note: Moving off any keypad or into the blank spaces is an error. 

<!--more-->

### (Failed) Version 1: Way over engineered

I'm just going to leave this here:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Keyboard {
    width: usize,
    height: usize,
    keys: Vec<Option<char>>,
}

impl From<&str> for Keyboard {
    fn from(value: &str) -> Self {
        let mut width = 0;
        let mut height = 0;
        let mut keys = Vec::new();

        for line in value.lines() {
            if line.is_empty() {
                continue;
            }

            height += 1;
            width = width.max(line.len());

            for c in line.chars() {
                if c.is_whitespace() {
                    continue;
                } else if c == '*' {
                    keys.push(None);
                } else {
                    keys.push(Some(c));
                }
            }
        }

        Self {
            width,
            height,
            keys,
        }
    }
}

impl Keyboard {
    fn get_key(&self, p: Point) -> Option<char> {
        if p.x < 0 || p.y < 0 || p.x >= self.width as i32 || p.y >= self.height as i32 {
            None
        } else {
            self.keys[p.y as usize * self.width + p.x as usize]
        }
    }

    fn get_point(&self, key: char) -> Option<Point> {
        for x in 0..self.width {
            for y in 0..self.height {
                let p: Point = (x, y).into();
                if self.get_key(p) == Some(key) {
                    return Some(p);
                }
            }
        }

        None
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
struct Typer<'kb> {
    keyboard: &'kb Keyboard,
    p: Point,
}

impl<'kb> Typer<'kb> {
    fn new(keyboard: &'kb Keyboard) -> Self {
        for x in 0..keyboard.width {
            for y in 0..keyboard.height {
                let p: Point = (x, y).into();
                if keyboard.get_key(p) == Some('A') {
                    return Self { keyboard, p };
                }
            }
        }

        panic!("keyboard does not contain 'A'");
    }

    fn go(&mut self, c: char) -> bool {
        self.p = self.p
            + match c {
                '^' => Direction::Up,
                'v' => Direction::Down,
                '<' => Direction::Left,
                '>' => Direction::Right,
                _ => {
                    return false;
                }
            };

        true
    }

    fn type_char_path(&mut self, target: char) -> String {
        let target_p = match self.keyboard.get_point(target) {
            Some(p) => p,
            None => panic!("could not find target"),
        };

        match astar(
            &(self.p, None),
            |&(p, _)| {
                let mut neighbors = Vec::new();

                Direction::all().into_iter().for_each(|d| {
                    if let Some(c) = self.keyboard.get_key(p + d) {
                        neighbors.push(((p + d, Some(d)), 1));
                    }
                });

                neighbors
            },
            |&(p, _)| p.manhattan_distance(&target_p),
            |&(p, _)| self.keyboard.get_key(p) == Some(target),
        ) {
            Some((path, _)) => {
                let &(last_p, _) = path.last().unwrap();
                self.p = last_p;

                path.iter()
                    .filter_map(|&(_, d)| match d {
                        Some(Direction::Up) => Some('^'),
                        Some(Direction::Down) => Some('v'),
                        Some(Direction::Left) => Some('<'),
                        Some(Direction::Right) => Some('>'),
                        _ => None,
                    })
                    .chain(std::iter::once('A'))
                    .collect()
            }
            None => panic!("could not find path to target"),
        }
    }

    fn type_string_path(&mut self, target: &str) -> String {
        target.chars().map(|c| self.type_char_path(c)).collect()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct TyperChain<'kbs> {
    me: Typer<'kbs>,
    next: Option<Rc<RefCell<TyperChain<'kbs>>>>,
}

impl<'kbs> std::hash::Hash for TyperChain<'kbs> {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.me.hash(state);
        if let Some(ref next) = self.next {
            next.borrow().hash(state);
        }
    }
}

impl<'kbs> TyperChain<'kbs> {
    fn new(keyboards: &'kbs [Keyboard]) -> Self {
        let me = Typer::new(&keyboards[0]);
        let next = if keyboards.len() > 1 {
            Some(Rc::new(RefCell::new(TyperChain::new(&keyboards[1..]))))
        } else {
            None
        };

        Self { me, next }
    }

    // Type a single char on this chain
    fn type_char(&mut self, c: char) -> Result<Option<char>, ()> {
        if c == 'A' {
            // An A sends activates the next robot in line
            // If there is none, return the A
            // This may recursively fail
            if let Some(next) = &self.next {
                return next.borrow_mut().type_char(c);
            } else {
                return Ok(Some('A'));
            }
        } else {
            // Any other character just updates this robot
            // If there is no next robot in line, it also emits the character
            // If we fail to move, that is our error case
            if self.me.go(c) {
                if self.next.is_none() {
                    return Ok(Some(self.me.keyboard.get_key(self.me.p).unwrap()));
                } else {
                    return Ok(None);
                }
            } else {
                Err(())
            }
        }
    }
}
```

I think I went slightly insane with this. 

We have a `Keyboard` which represents the layout of the keys, a `Typer` which controls a keyboard (so it's cheaper to `clone`), and a `TyperChain`, which is several of those chained together. All together, it's a bonkers combination--especially when I was actually keeping lifetimes around so I wasn't making a ton of different copies of the keyboards. 

On top of that, I was going to throw A-Star at it once again, with this as a successor function. Turns out just about any puzzle is a graph traversal problem if you stare at it hard enough. :smile:"

```rust
let successors = |(chain, index): &State<'_, 'kbs>| {
    let mut next = vec![];

    for c in KEYS {
        let mut new_chain = chain.clone();
        match new_chain.type_char(c) {
            Ok(Some(c)) => {
                // If we typed the correct next char, continue
                // If we typed something else, this is an invalid branch
                if c == target_chars[*index] {
                    next.push(((new_chain, index + 1), 1));
                } else {
                    continue;
                }
            }
            Ok(None) => {
                // Advanced but did not type anything
                next.push(((new_chain, *index), 1));
            }
            Err(()) => {
                // Failed to advance somewhere along the line, this is an invalid branch
                continue;
            }
        }
    }

    next
};
```

It's... a mess and didn't end up working. :smile:

### Version 2: Direct simulation

Okay, so I scrapped all that, but kept the basic idea. This time, I'll keep the entire state encapsulated as a `Vec<Point>`, which is the ordered position on each keyboard as we go along the line. 

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct State {
    points: Vec<Point>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Day21Error {
    InvalidDirection,
    OutOfBounds,
    InvalidPosition,
}

impl State {
    fn new(arrow_robots: usize) -> State {
        let mut points = Vec::new();

        for _ in 0..arrow_robots {
            points.push(Point::new(2, 0));
        }
        points.push(Point::new(2, 3));

        State { points }
    }

    #[tracing::instrument]
    fn hit(&self, c: char) -> Result<(State, Option<char>), Day21Error> {
        let mut new_points = self.points.clone();

        let mut c = c;
        for i in 0..new_points.len() {
            tracing::debug!("In level {i}, c={c}");

            let keys = if i == new_points.len() - 1 {
                KEYPAD
            } else {
                ARROWS
            };
            let height = if i == new_points.len() - 1 { 4 } else { 2 };
            let index = (new_points[i].y * 3 + new_points[i].x) as usize;

            if c == 'A' {
                // Type that character on the next level
                c = keys[index];
            } else {
                // Try to move this layer
                let d: Direction = c.try_into().map_err(|_| Day21Error::InvalidDirection)?;
                let new_point = new_points[i] + d;

                // Out of bounds
                if new_point.x < 0 || new_point.x >= 3 || new_point.y < 0 || new_point.y >= height {
                    return Err(Day21Error::OutOfBounds);
                }

                // Moved to an invalid character
                let new_index = (new_point.y * 3 + new_point.x) as usize;
                if keys[new_index] == '*' {
                    return Err(Day21Error::InvalidPosition);
                }

                // Otherwise, we're done without outputting a character
                new_points[i] = new_point;
                return Ok((State { points: new_points }, None));
            }
        }

        // If we made it out of the list, we typed whatever is left in c
        Ok((State { points: new_points }, Some(c)))
    }
}
```

The `for i in 0..new_points.len()` is the core of the algorithm. Basically, it's looping through each layer. If you ever type an `A`, that means we've got to process the next level down. Otherwise, you only update a pointer and break the recursion (so most of the time, we don't loop the entire way). 

This... took a while to get exactly right. Thus the slightly more fleshed out `Day21Error` types (which also lets me use the `?` operator) and using {{<crate tracing>}}. 

But it does work!

```bash
$ cargo aoc --day 21 --part 1

AOC 2024
Day 21 - Part 1 - sim : 205160
	generator: 250ns,
	runner: 6.171459ms
```

We'll do better [after part 2](#part-1-continued).

## Part 2

> Instead of 2 intermediate sets of arrow keys, you have 25. 

...

That's a lot. 

I didn't even try the direct simulation to see how long it would possibly take to solve this problem with A*. Instead, let's use a couple of facts we know about the simulation:

* It's always better to hit the same button more times in a row (`<v<` is slower than `<<v`). This is because to hit `<<`, the next level up can just hit an extra `A` without having to move while `<v<` would require `>A` to move from `<` to `v` and another `<A` to move back to `<`. When you chain that up 25 layers, that's huge savings. 

So for any difference in points, we'll always want to either move horizontally than vertically or vice versa. 

This is going to be most important when it comes down the the lowest level, moving around on the numpad/keypad:

```rust
// For each numpad key, where is it?
#[tracing::instrument(ret)]
fn keypad_position(key: char) -> (usize, usize) {
    match key {
        '7' => (0, 0),
        '8' => (1, 0),
        '9' => (2, 0),
        '4' => (0, 1),
        '5' => (1, 1),
        '6' => (2, 1),
        '1' => (0, 2),
        '2' => (1, 2),
        '3' => (2, 2),
        // missing bottom left key
        '0' => (1, 3),
        'A' => (2, 3),
        _ => panic!("Invalid key"),
    }
}

// Generate sequences of ^v<>A that will move from src to dst on the keypad
#[tracing::instrument(ret)]
fn keypad_paths(src: char, dst: char) -> Vec<String> {
    // Convert to points
    let (x1, y1) = keypad_position(src);
    let (x2, y2) = keypad_position(dst);

    // If we're move left/up, use <^; otherwise >V (deal with zero later)
    let h_char = if x1 < x2 { '>' } else { '<' };
    let v_char = if y1 < y2 { 'v' } else { '^' };

    let h_delta = (x2 as isize - x1 as isize).abs();
    let h_string = std::iter::repeat_n(h_char, h_delta as usize).collect::<String>();

    let v_delta = (y2 as isize - y1 as isize).abs();
    let v_string = std::iter::repeat_n(v_char, v_delta as usize).collect::<String>();

    // If we only have one of the two, then our path is simple :smile:
    // (This avoids duplicate paths in the _ case below)
    if h_delta == 0 || v_delta == 0 {
        return vec![format!("{h_string}{v_string}A")];
    }

    match (x1, y1, x2, y2) {
        // Moving from the bottom to the left
        // Avoid the missing square by going up first
        (_, 3, 0, _) => vec![format!("{v_string}{h_string}A")],
        // Moving from the left to the bottom
        // Avoid the missing square by going right first
        (0, _, _, 3) => vec![format!("{h_string}{v_string}A")],
        // Otherwise, try both
        _ => {
            let vh = format!("{v_string}{h_string}A");
            let hv = format!("{h_string}{v_string}A");
            vec![vh, hv]
        }
    }
}
```

First, we define where each point is, then we define a series of key presses we'd have to enter on the last level arrow keys in order to go from any one key to another at the lowest level. 

There are the two mentioned edge cases to avoid the missing space on the `keypad` and a simplification if we're moving straight in a direction rather than diagonally: only return one instead of both cases. 

So if we have to print `029A`, we have (note: we always start at `A`):

* `A` to `2`: `^<A` or `<^A`
* `2` to `9`: `^^>A` or `>^^A`
* `9` to `A`: only `vvv`

Next, we use that to set up the cost of entering a sequence on the `keypad` with some number of `arrows`:

```rust
// To move a given sequence of characters with that many arrow bots
#[tracing::instrument(ret)]
fn keypad_cost(input: &str, arrow_bots: usize) -> usize {
    // Assume we're starting at A
    // For each pair of characters, find the minimum path between them recursively
    format!("A{}", input)
        .chars()
        .tuple_windows()
        .map(|(src, dst)| {
            tracing::info!(
                "arrows cost outer map src={src}, dst={dst} with arrow_bots={arrow_bots}"
            );
            keypad_paths(src, dst)
                .iter()
                .map(|path| {
                    tracing::info!(
                        "arrow costs inner map path={path} with arrow_bots={arrow_bots}"
                    );
                    if arrow_bots == 0 {
                        path.len()
                    } else {
                        arrows_cost(path, arrow_bots)
                    }
                })
                .min()
                .unwrap()
        })
        .sum()
}
```

From the outside in, we're going to start by adding the `A` (as I mentioned, always start with `A`) and then looping over each pair (`tuple_windows` is from {{<crate itertools>}} and is like `ls.iter().zip(ls.iter().skip(1))`, but more concise. 

Next, we go through each possible path from those two keys. This will always be either 1 or 2 lists. For each of that sequences, we'll pass off to another function (`arrows_cost`, coming soon) to do the actual recursion. 

And now the actually recursive bits: implementing a stack of `arrows`:

```rust
// Generate sequences of movements on the arrow keys
#[tracing::instrument(ret)]
fn arrows_paths(src: char, dst: char) -> Vec<String> {
    // For any square one away, go directly
    // For any two away, return both options
    match (src, dst) {
        ('^', 'A') => vec![">A"],
        ('^', '<') => vec!["v<A"],
        ('^', 'v') => vec!["vA"],
        ('^', '>') => vec![">vA", "v>A"],

        ('A', '^') => vec!["<A"],
        ('A', '<') => vec!["v<<A"],
        ('A', 'v') => vec!["<vA", "v<A"],
        ('A', '>') => vec!["vA"],

        ('<', '^') => vec![">^A"],
        ('<', 'A') => vec![">>^A"],
        ('<', 'v') => vec![">A"],
        ('<', '>') => vec![">>A"],

        ('v', '^') => vec!["^A"],
        ('v', 'A') => vec!["^>A", ">^A"],
        ('v', '<') => vec!["<A"],
        ('v', '>') => vec![">A"],

        ('>', '^') => vec!["<^A", "^<A"],
        ('>', 'A') => vec!["^A"],
        ('>', '<') => vec!["<<A"],
        ('>', 'v') => vec!["<A"],

        // I had a heck of a time debugging in here... v =/= V
        (a, b) if a == b => vec!["A"],
        (a, b) => panic!("Bad encoding for {a} -> {b}"),
    }
    .iter()
    .map(|&s| s.to_owned())
    .collect()
}

// To move level 0 from (x, y) to (x + xd, y + yd), what do we need to do at this level?
#[tracing::instrument(ret)]
fn arrows_cost(input: &str, arrow_bots: usize) -> usize {
    // If we don't have any more arrow bots, it's easy :smile:
    if arrow_bots == 0 {
        return input.len();
    }

    // Otherwise, assume we're starting at A
    // For each pair of characters, find the minimum path between them with one less bot
    format!("A{}", input)
        .chars()
        .tuple_windows()
        .map(|(src, dst)| {
            tracing::info!("keypad cost mapping src={src}, dst={dst}");
            arrows_paths(src, dst)
                .iter()
                .map(|path| arrows_cost(path, arrow_bots - 1))
                .min()
                .unwrap()
        })
        .sum()
}
```

Deceptively simple. :smile:

Basically, we once again do all the combinations of keys, although this time I just hard coded them. We are always either moving to an adjacent key (in which case there's one path), a one step diagonal (two paths), or from `<` to/from `A` (one path that keeps the `<<` or `>>` together and avoids the empty space). 

Then for the recursive function, we go again for each `tuple_windows` of `<>^vA` that we generated either one layer up or in the `keypad_cost`, and recursively ask what's the best way that we could generate that sequence. 

It's kind of amazing how relatively little code this ended up being. We can use it to directly implement either part 1 or 2:

```rust
#[aoc(day21, part1, recur)]
fn part1_recur(input: &str) -> usize {
    input
        .lines()
        .map(|line| line_multiplier(line) * keypad_cost(line, 2))
        .sum()
}

#[aoc(day21, part2, recur)]
fn part2_recur(input: &str) -> usize {
    input
        .lines()
        .map(|line| line_multiplier(line) * keypad_cost(line, 25))
        .sum()
}
```

For part 1, we get *significant* speedup:

```bash
$ cargo aoc --day 21 --part 1

AOC 2024
Day 21 - Part 1 - sim : 205160
	generator: 250ns,
	runner: 6.171459ms

Day 21 - Part 1 - recur : 205160
	generator: 208ns,
	runner: 120.084µs
```

Mostly, we're not actually calculating the lists, but just the counts (which is what we needed). 

Unfortunately, this *still* isn't fast enough to solve part 2. But this is fixable, since we know we're doing a *ton* of repeated work. Once we've figured out how to go from `<` to `>` halfway down the stack once... we can do that over and over again and it will always be the same length. 

### Memoization

So of course, we're going to add `memoization`.

Basically, all we have to do is introduce a cache, pass it through the other `keyboard_cost` layer and then use it in the `arrows_cost` functions:

```rust
type CacheType = HashMap<(String, usize), usize>;

// To move level 0 from (x, y) to (x + xd, y + yd), what do we need to do at this level?
// This function is the one we actually memoize
#[tracing::instrument(ret)]
fn arrows_cost_memo(cache: &mut CacheType, input: &str, arrow_bots: usize) -> usize {
    // If we don't have any more arrow bots, it's easy :smile:
    if arrow_bots == 0 {
        return input.len();
    }

    // Already cached
    // NOTE: This is expensive, since I'm cloning a ton of strings and hashing
    //       But when the alternative is branching trillions of times...
    let cache_key = (input.to_owned(), arrow_bots);
    if let Some(&value) = cache.get(&cache_key) {
        return value;
    }

    // Otherwise, assume we're starting at A
    // For each pair of characters, find the minimum path between them with one less bot
    let result = format!("A{}", input)
        .chars()
        .tuple_windows()
        .map(|(src, dst)| {
            tracing::info!("keypad cost mapping src={src}, dst={dst}");
            arrows_paths(src, dst)
                .iter()
                .map(|path| arrows_cost_memo(cache, path, arrow_bots - 1))
                .min()
                .unwrap()
        })
        .sum();

    cache.insert(cache_key, result);
    result
}

// To move a given sequence of characters with that many arrow bots
// This function exists entirely to call arrows_cost_memo with the cache
#[tracing::instrument(ret)]
fn keypad_cost_memo(cache: &mut CacheType, input: &str, arrow_bots: usize) -> usize {
    // Assume we're starting at A
    // For each pair of characters, find the minimum path between them recursively
    format!("A{}", input)
        .chars()
        .tuple_windows()
        .map(|(src, dst)| {
            tracing::info!(
                "arrows cost outer map src={src}, dst={dst} with arrow_bots={arrow_bots}"
            );
            keypad_paths(src, dst)
                .iter()
                .map(|path| {
                    tracing::info!(
                        "arrow costs inner map path={path} with arrow_bots={arrow_bots}"
                    );
                    if arrow_bots == 0 {
                        path.len()
                    } else {
                        arrows_cost_memo(cache, path, arrow_bots)
                    }
                })
                .min()
                .unwrap()
        })
        .sum()
}
```

And build and pass in the caches:

```rust
#[aoc(day21, part1, memo)]
fn part1_recur_memo(input: &str) -> usize {
    let mut cache = CacheType::new();

    input
        .lines()
        .map(|line| line_multiplier(line) * keypad_cost_memo(&mut cache, line, 2))
        .sum()
}

#[aoc(day21, part2, memo)]
fn part2_recur_memo(input: &str) -> usize {
    let mut cache = CacheType::new();

    input
        .lines()
        .map(|line| line_multiplier(line) * keypad_cost_memo(&mut cache, line, 25))
        .sum()
}
```

One interesting bit is that we *specifically* want to keep the cache across input runs, since we're going to end up doing much of the same work on any level higher than the `keypad` itself. You're always moving from `<` to `>` halfway up somewhere in the problem, so cache it between runs. 

So how's it do for part 1?

```bash
$ cargo aoc --day 21 --part 1

AOC 2024
Day 21 - Part 1 - sim : 205160
	generator: 250ns,
	runner: 6.171459ms

Day 21 - Part 1 - recur : 205160
	generator: 208ns,
	runner: 120.084µs

Day 21 - Part 1 - memo : 205160
	generator: 20.042µs,
	runner: 76.708µs
```

Not bad. But the real magic comes in part 2!

```rust
$ cargo aoc --day 21 --part 2

AOC 2024
Day 21 - Part 2 - memo : 252473394928452
	generator: 27.917µs,
	runner: 582.166µs
```

Why yes, that is in fact a very large number. 

Breaking it out a bit more, each three digit plus `A` code took 8-10 **billion** keystrokes to enter. 

What's kind of crazier (and more awesome) to me is:

```text
line 1, cache size: 362
line 2, cache size: 370
line 3, cache size: 375
line 4, cache size: 378
line 5, cache size: 380
```

After the first solved problem, we've only put 362 items in our cache. This is because there are only 16 different strings we're going to do at any specific step on `arrows_cost`:

```text
1   <<A
3   <A
1   <^A
1   <vA
1   >>A
1   >>^A
3   >A
2   >^A
1   >vA
1   ^<A
1   ^>A
2   ^A
1   v<<A
2   v<A
1   v>A
2   vA
```

That times 25 layers means that our maximum cache size is only 400. 

So we've gotten 362 in the first iterations and only add 12 the second, then 3, 2, 2. So much repeated work!

No wonder it's sub millisecond to (show that you need to) count to ten billion 4 times. :smile:


## Benchmarks

```bash
# With tracing
$ cargo aoc bench --day 21

Day21 - Part1/sim       time:   [1.7863 ms 1.7963 ms 1.8074 ms]
Day21 - Part1/recur     time:   [45.440 µs 45.715 µs 46.027 µs]
Day21 - Part1/memo      time:   [20.319 µs 20.428 µs 20.556 µs]

Day21 - Part2/memo      time:   [180.37 µs 180.69 µs 181.02 µs]
```

### Tracing

The {{<crate tracing>}} is awesome. It reminds me of [`racket/trace`](https://docs.racket-lang.org/reference/debugging.html) from my Racket days. A simple change and you get tracing over recursive functions basically for free. 

I was actually surprised at how little impact it had on the overall timing:

```bash
# Removing tracing calls entirely
$ cargo aoc bench --day 21

Day21 - Part1/sim       time:   [1.3800 ms 1.3844 ms 1.3888 ms]
Day21 - Part1/recur     time:   [46.511 µs 49.849 µs 56.418 µs]
Day21 - Part1/memo      time:   [19.496 µs 19.621 µs 19.772 µs]

Day21 - Part2/memo      time:   [157.90 µs 158.17 µs 158.44 µs]
```

Now don't get me wrong, there *is* a measurable cost, but it's well within the same order of magnitude. What's interesting though is that you can also use [level filters](https://docs.rs/tracing/latest/tracing/level_filters/index.html) to turn that off as a `Cargo.toml` feature flag:

```bash
$ cargo add tracing -F release_max_level_off
```

From the documentation: 

> Trace verbosity levels can be statically disabled at compile time via Cargo features, similar to the log crate. Trace instrumentation at disabled levels will be skipped and will not even be present in the resulting binary unless the verbosity level is specified dynamically.

This should mean that all of the tracing macros I added are not compiled into our binary in `release` mode. 

That's it, now we run it again:

```bash
# Keep tracing calls + remove with -F release_max_level_off
$ cargo aoc bench --day 21

Day21 - Part1/sim       time:   [1.4110 ms 1.4204 ms 1.4316 ms]
Day21 - Part1/recur     time:   [32.581 µs 32.933 µs 33.459 µs]
Day21 - Part1/memo      time:   [15.031 µs 15.263 µs 15.601 µs]

Day21 - Part2/memo      time:   [125.56 µs 127.00 µs 128.95 µs]
```

I'm not 100% sure what's going on here, although I'll dig into it more. By two guesses are:

1. This will also disable tracing in libraries I'm using
2. I previously had the `-F log -F log-always` features of {{<crate tracing>}} still enabled; so it could have been generating log messages (even though I didn't look at them)

To see that:

```bash
# Tracing with -F log -F log-always -F release_max_level_off
$ cargo aoc bench --day 21

Day21 - Part1/sim       time:   [1.7860 ms 1.8005 ms 1.8220 ms]
Day21 - Part1/recur     time:   [46.033 µs 46.552 µs 47.321 µs]
Day21 - Part1/memo      time:   [20.111 µs 20.190 µs 20.282 µs]

Day21 - Part2/memo      time:   [163.49 µs 165.21 µs 167.94 µs]
```

To compare more directly, we have:

| Name        | With tracing | Removed   | `log,log-always` | `release_max_level_off` |
| ----------- | ------------ | --------- | ---------------- | ----------------------- |
| Part1/sim   | 1.7963 ms    | 1.3844 ms | 1.8005 ms        | 1.4204 ms               |
| Part1/recur | 45.715 µs    | 49.849 µs | 46.552 µs        | 32.933 µs               |
| Part1/memo  | 20.428 µs    | 19.621 µs | 20.190 µs        | 15.263 µs               |
| Part2/memo  | 180.69 µs    | 158.17 µs | 165.21 µs        | 127.00 µs               |

I wonder how much of that is just noise, even though I am doing `aoc bench` with it's 100 iterations. It's just such a quick program and (as noted in [the memo section](#memoization)) it's not actually doing that many recursive calls by the end of it. 

If anyone has more experience with the whole thing, I'd love to hear it. It's not really that critical for most large scale applications (you will want logging far more than a tiny bit of performance for most cases), but it's fascinating to me. 