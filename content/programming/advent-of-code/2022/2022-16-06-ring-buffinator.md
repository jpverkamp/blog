---
title: "AoC 2022 Day 6: Ring Buffinator"
date: 2022-12-06 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
---
### Source: [Tuning Trouble](https://adventofcode.com/2022/day/6)

#### **Part 1:** Given input as a list of characters, find the index of the first {{<wikipedia "sliding window">}} (size 4) where all of the characters are distinct.

<!--more-->

This sounds like a perfect excuse for a {{<wikipedia "ring buffer">}}. Let's implement one!

```rust
#[derive(Debug)]
struct CharRingBuffer {
    size: usize,
    head: usize,
    count: usize,
    data: Vec<char>,
}

impl CharRingBuffer {
    pub fn new(size: usize) -> Self {
        let mut data = Vec::new();
        for _ in 0..size {
            data.push('\0');
        }

        CharRingBuffer{ size, head: 0, count: 0, data }
    }

    pub fn push(&mut self, c: char) {
        self.data[self.head] = c;
        self.head = (self.head + 1) % self.size;

        if self.count < self.size {
            self.count += 1
        }
    }

    pub fn len(&self) -> usize {
        self.count
    }
}

impl<'a> CharRingBuffer {
    pub fn iter(&'a self) -> impl Iterator<Item = &'a char> {
        self.data.iter()
            .chain(self.data.iter())
            .skip(self.head)
            .take(self.count)
    }
}
```

In a nutshell, we have a constant number of values that we can actually store in the buffer. 

Those could definitely be stored in an array (since the size doesn't change)... but unfortunately it seems like Rust doesn't currently support parameterizing an array's size within a struct. 

I could use a macro to generate it, but I haven't touched Rust macros yet. I certainly do want to, but I don't believe now is the time. 

So, that's the struct. `head` is the index that we'll next modify, `size` is the maximum numbers to store, and `count` is the current actual number in the ring buffer. 

Next, we implement `iter` over the ring buffer. This is pretty neat, since we can build the iter directly off the vector of `data`. Specifically, `chain` two copies (since we'll wrap most times), `skip` over values before the `head`, and `take` the current number we have. That will return an iterator itself. 

The one interesting (very Rusty) bit here is the lifetime parameter ```a``. All that means is that the iterator and all items returns by it will live as long as the ring buffer itself does. That makes sense to me!

Okay, next part, let's actually use the ring buffer. We want to take in an input string, shove characters into a ring buffer, and check each time to see if we have an non-duplicate set yet:

```rust
fn first_duplicate_at(line: &String, size: usize) -> Option<usize> {
    let mut crb = CharRingBuffer::new(size);
    
    for (i, c) in line.chars().enumerate() {
        crb.push(c);
        if crb.len() < size {
            continue;
        }

        let mut s = HashSet::new();
        for c in crb.iter() {
            s.insert(c);
        }

        if s.len() == size {
            return Some(i + 1);
        }
    }

    None
}
```

That's not bad at all. I would have liked to have something like [`itertools.all_unique`](https://docs.rs/itertools/latest/itertools/trait.Itertools.html#method.all_unique), but not enough to actually pull in an external crate. Perhaps another time, this does the same. 

Finally, we do always assume the input is value and we'll have a value, but I'm going to return an `Option` anyways, since otherwise what do we return at the end? We could do a {{<wikipedia "sentinel value">}}... but that's why `Option` exists in the first place. 

With that, one more wrapper to support reading any number of lines and processing them:

```rust
fn part1(filename: &Path) -> String {
    let mut result = String::new();

    for line in read_lines(filename) {
        let index = first_duplicate_at(&line, 4).expect("must have a duplicate").to_string();
        result.push_str(&index);
        result.push('\n');
    }
    
    String::from(result.strip_suffix('\n').expect("must return at least one value"))
}
```

And we're done. I didn't need to do that for my main problem, but I put multiple test cases in my `06-test.txt` file and this lets me deal with that. 

#### **Part 2:** Do the same with a ring buffer size of 14. 

Abstraction for the win!

```rust
fn part2(filename: &Path) -> String {
    let mut result = String::new();

    for line in read_lines(filename) {
        let index = first_duplicate_at(&line, 14).expect("must have a duplicate").to_string();
        result.push_str(&index);
        result.push('\n');
    }
    
    String::from(result.strip_suffix('\n').expect("must return at least one value"))
}
```

Literally just add 1 character. I guess I could have abstracted that, but :shrug:

#### Performance

```bash
$ ./target/release/06-ring-bufferinator 1 data/06.txt

1760
took 1.02625ms

$ ./target/release/06-ring-bufferinator 2 data/06.txt

2974
took 2.469375ms
```

I feel like there's probably some small penalties to constantly building and tearing down the `HashSet`s, plus using an array rather than a `Vec` could have some better cache performance. But... it still runs in 1-3 ms. So... I'm not going to optimize this one any more just yet.

Onward!