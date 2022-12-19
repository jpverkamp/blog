---
title: "AoC 2022 Day 14: Sandinator"
date: 2022-12-14 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Regolith Reservoir](https://adventofcode.com/2022/day/14)

## Part 1

> Given a series of walls as input, run a {{<wikipedia "falling sand">}} simulation until any new sand falls of the map. Count how many grains of sand we end up with. 

<!--more-->

Oh, how I love falling sand. 

First, the struct we're going to use to represent our current simulation:

```rust
#[derive(Debug)]
struct Sandbox {
    active_sand: HashSet<Point>,
    settled_sand: HashSet<Point>,
    walls: HashSet<Point>,

    min_x: isize,
    max_x: isize,
    min_y: isize,
    max_y: isize,
}
```

The `(min|max)-(x|y)` are entirely for display purposes. Otherwise, `walls` are static pieces that stop the sand, `active_sand` is still falling, and `settled_sand` is not. 

The original problem states:

> Sand is produced one unit at a time, and the next unit of sand is not produced until the previous unit of sand comes to rest. A unit of sand is large enough to fill one tile of air in your scan.

But I had a feeling that wasn't going to be strictly necessary. So I made it possible for more than one grain to fall at a time. We'll come back to that. 

Before that, parsing:

```rust
impl<I> From<&mut I> for Sandbox
where
    I: Iterator<Item = String>,
{
    fn from(iter: &mut I) -> Self {
        let mut walls = HashSet::new();
        let mut min_x = isize::MAX;
        let mut max_x = isize::MIN;
        let mut min_y = isize::MAX;
        let mut max_y = isize::MIN;

        for line in iter {
            let mut p = Point { x: 0, y: 0 };
            let mut first = true;

            for part in line.split(" -> ") {
                let mut xy = part.split(",");
                let new_p = Point {
                    x: xy
                        .next()
                        .expect("must have x")
                        .parse::<isize>()
                        .expect("x must be numeric"),
                    y: xy
                        .next()
                        .expect("must have x")
                        .parse::<isize>()
                        .expect("y must be numeric"),
                };

                if !first {
                    let delta = Point {
                        x: (new_p.x - p.x).signum(),
                        y: (new_p.y - p.y).signum(),
                    };

                    // Rather than while p != new_p, do this to get both edge cases
                    let mut done = false;
                    loop {
                        walls.insert(p);
                        min_x = isize::min(min_x, p.x - 1);
                        max_x = isize::max(max_x, p.x + 1);
                        min_y = isize::min(min_y, p.y - 1);
                        max_y = isize::max(max_y, p.y + 1);

                        if done {
                            break;
                        }

                        p = p + delta;
                        if p == new_p {
                            done = true;
                        }
                    }
                }

                p = new_p;
                first = false;
            }
        }

        Sandbox {
            active_sand: HashSet::new(),
            settled_sand: HashSet::new(),
            walls,
            min_x,
            max_x,
            min_y,
            max_y,
        }
    }
}
```

It's a bit long, but the input is a little weird. Each input line is a sequence of straight lines and we have to iterate between them. But we only do this once, so it can be a bit heavy. 

Next up, we actually implement the simulation:

```rust
impl Sandbox {
    fn occupied(&self, p: Point) -> bool {
        self.walls.contains(&p) || self.settled_sand.contains(&p) || self.active_sand.contains(&p)
    }

    fn drop(&mut self, p: Point) {
        if self.occupied(p) {
            return;
        }

        self.min_x = isize::min(self.min_x, p.x - 1);
        self.max_x = isize::max(self.max_x, p.x + 1);
        self.min_y = isize::min(self.min_y, p.y - 1);
        self.max_y = isize::max(self.max_y, p.y + 1);

        self.active_sand.insert(p);
    }

    fn step(&mut self) -> bool {
        let mut next_active_sand = HashSet::new();

        for p in self.active_sand.iter() {
            // If we're past the lowest value, drop this point
            if p.y > self.max_y {
                return true;
            }

            // Otherwise, try to fall (first left than right)
            let nexts = vec![
                *p + Point::DOWN,
                *p + Point::DOWN + Point::LEFT,
                *p + Point::DOWN + Point::RIGHT,
            ];

            let mut moved = false;
            for next in nexts.into_iter() {
                if !self.occupied(next) && !next_active_sand.contains(&next) {
                    next_active_sand.insert(next);
                    moved = true;
                    break;
                }
            }

            // If we can't fall, settle
            if !moved {
                self.settled_sand.insert(*p);
            }
        }

        self.active_sand = next_active_sand;
        false
    }
}
```

This doesn't actually care at all if there is one grain of sand or a million. The main idea is that we have a double buffer for `active_sand`. We're going to iterate over all the sand, but each point can collide with:

* `walls`
* `settled_sand`
* `active_sand` - this is the sand that was there at the beginning of the frame
* `next_active_sand` - this is sand that has already moved this frame, to avoid two moving to the same spot

Once we've iterated over everything, we can swap `active_sand` and continue on the next frame.

Finally, `part1` to actually control the simulation:

```rust
fn part1(filename: &Path) -> String {
    let mut sandbox = Sandbox::from(&mut iter_lines(filename));
    let drop = Point { x: 500, y: 0 };

    for _frame in 1.. {
        if sandbox.active_sand.is_empty() {
            sandbox.drop(drop);
        }

        let done = sandbox.step();
        if done {
            break;
        }
    }

    sandbox.settled_sand.len().to_string()
}
```

Not much there. And I can even make a pretty simulation:

<video controls src="/embeds/2022/aoc14-old-1.mp4"></video>

I'll come back to how I actually made that. 

But this does make me think... why in the world are we actually doing a single grain of sand at a time? They only interact if they're right behind each other, so why don't we:

```rust
fn part1(filename: &Path) -> String {
    let mut sandbox = Sandbox::from(&mut iter_lines(filename));
    let drop = Point { x: 500, y: 0 };

    for frame in 1.. {
        if frame % 2 == 0 {
            sandbox.drop(drop);
        }

        let done = sandbox.step();
        if done {
            sandbox.active_sand.clear();
            break;
        }
    }

    sandbox.settled_sand.len().to_string()
}
```

<video controls src="/embeds/2022/aoc14-1.mp4"></video>

It turns out... exactly the same. 

Once a single grain has fallen out of the simulation, we know all the rest of the `active_sand` will as well, so clear it and return. And we get the same thing, only much much faster. 

Well, check `performance` for how much faster. It turns out Rust is *really* fast, so it's not actually that much better. But it really did help with rendering that movie up there. Since we have significantly fewer frames, it's much easier to deal with. 

## Part 2

> Add an infinite floor two pixels below the previous lower bound. Count the settled sand again. 

```rust
fn part2(filename: &Path) -> String {
    let mut sandbox = Sandbox::from(&mut iter_lines(filename));
    let drop = Point { x: 500, y: 0 };

    // We want a line from -infinity,max_y+1 to +infinity,max_y
    // We don't actually need that though, just out at a 45 angle from min_x,min_y and max_x,min_y
    // Add some buffer for the extra offsets we're dealing with
    let height = sandbox.max_y - sandbox.min_y;
    let left_x = sandbox.min_x - height - 10;
    let right_x = sandbox.max_x + height + 10;

    for x in left_x..=right_x {
        sandbox.walls.insert(Point {
            x,
            y: sandbox.max_y + 1,
        });
    }
    sandbox.min_x = left_x - 1;
    sandbox.max_x = right_x + 1;
    sandbox.max_y += 2;

    for frame in 1.. {
        if frame % 2 == 0 {
            sandbox.drop(drop);
        }

        let done = sandbox.step();
        if done || sandbox.occupied(drop) {
            sandbox.active_sand.clear();
            break;
        }
    }

    sandbox.settled_sand.len().to_string()
}
```

As noted, we don't actually need to make the infinite line. Because sand stacks at 45 degrees, we only need to go out from our current min and max by the total height (at worst case). So to handle all that, we add the new wall and update the bounds. Voila. 

Here is where the optimization really comes in handy. It turns out that it takes roughly 1.5 million steps to solve one grain at a time. If you're rendering each of those to a single file... that's not going to go well. Well, it *didn't* go well. But if you do every other frame, it only takes ~50k frames. So much more feasible. 

<video controls width="100%" src="/embeds/2022/aoc14-2.mp4"></video>

I *tried* to render the full thing to a video... but turning 1.5M pngs into a video... didn't go well. So only one for you this time. And it's still pretty slow once it gets to the final fill. 

## Performance

Here are the numbers for both one at a time and every other frame. 

```bash
# Drop one sand at a time

$ ./target/release/14-sandinator 1 data/14.txt

698
took 27.268ms

$ ./target/release/14-sandinator 2 data/14.txt

28594
took 904.257791ms

# Drop one sand every other frame

$ ./target/release/14-sandinator 1 data/14.txt

698
took 28.331666ms

$ ./target/release/14-sandinator 2 data/14.txt

28594
took 633.109583ms
```

There's actually not much speed up in the small case, Rust is fast. But we do cut 1/3 of the runtime off in the longer case, since that's just a lot of sand. Still under a second though!

#### Pretty (moving) pictures

Okay, let's actually talk about generating the images. In a nutshell, I pulled in the [`image`](https://docs.rs/image/latest/image/) crate. That lets us render a pixel `from_fn`, something I've done an awful lot in Racket:

```rust
impl Sandbox {
    fn render(&self) -> RgbImage {
        let width = (self.max_x - self.min_x) as u32;
        let height = (self.max_y - self.min_y) as u32;

        ImageBuffer::from_fn(width, height, |x, y| {
            let p = Point {
                x: (x as isize) + self.min_x,
                y: (y as isize) + self.min_y,
            };
            if self.walls.contains(&p) {
                image::Rgb([127, 127, 127])
            } else if self.settled_sand.contains(&p) {
                image::Rgb([194, 178, 128])
            } else if self.active_sand.contains(&p) {
                image::Rgb([255, 255, 255])
            } else {
                image::Rgb([0, 0, 0])
            }
        })
    }
}
```

That really is it. To actually combine it into a video, I directly Shelled out to `ffmpeg`:

```rust
fn make_gif() {
    use std::process::Command;

    let commands = vec![
        "ffmpeg -y -framerate 240 -i %08d.png -vf scale=iw*4:ih*4:flags=neighbor -c:v libx264 -r 30 sandbox.mp4",
        "find . -name '*.png' | xargs rm"
    ];

    for cmd in commands.into_iter() {
        println!("$ {}", cmd);
        let mut child = Command::new("bash")
            .arg("-c")
            .arg(cmd)
            .spawn()
            .expect("command failed");
        child.wait().expect("process didn't finish");
    }
}
```

Yes, using `bash -c` this way is a prime candidate for Shell injection, but... it's not like I'm dealing with any non-constant params in this case, so it's really a pretty minimal risk. And much easier to write. 

And that's it. Pretty (moving) pictures. 

#### A lesson in filesystem limitations

It turns out filesystems *really* don't like having 1.5M files in them. Finder freaked out, VS Code crashed, and I couldn't even `ls` or run `find` on the directory to delete the files. 

What finally did end up working was installing [`fd`](https://github.com/sharkdp/fd) (more Rust!) and using that to delete the files in batches:

```bash
$ for i in $(seq 1 100); do
    echo $i;
    fd -g '*.png' | head -n 10000 | xargs rm;
done
```

That took a little while, but it didn't actually hang and I got my machine back. I've done this before... but it's been a while. 

#### A lesson in web compatibility  

So... the original videos (above) didn't render well at all. I had to run them through a bit more `ffmpeg` magic to get them to play in a browser:

```bash
$ for f in *.mp4; do
    echo $f;
    bak $f;
    ffmpeg -y 
        -i $f.bak 
        -c:v libx264 
        -preset slow 
        -crf 20 
        -vf format=yuv420p 
        -movflags +faststart 
        $f;
done
```

Finally. 