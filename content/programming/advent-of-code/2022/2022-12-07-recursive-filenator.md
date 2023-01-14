---
title: "AoC 2022 Day 7: Recursive Fileinator"
date: 2022-12-07 00:00:03
programming/languages:
- Rust
programming/sources:
- Advent of Code
series:
- Advent of Code 2022
programming/topics:
- File Systems
---
## Source: [No Space Left On Device](https://adventofcode.com/2022/day/7)

## Part 1

> Give the output of a very simple shell with only the commands `cd` and `ls` (the output of which is either `"dir" name` for directories or `size name` for files), find the largest directory (disk usage calculated recursively) with a size no greater than 100,000. 

<!--more-->

Oh boy this one was crazy. Rust does some... *interesting* things when it comes to recursive/self-referential data structures. 

Specifically, here's where I ended up:

```rust
// Represents a 'thing' on a file system, either:
//  - A named directory which can contain directories or files
//  - A named file which has a size
#[derive(Clone)]
enum FileSystemThing {
    Directory {
        name: String,
        parent: Option<Arc<FileSystemThing>>,
        children: RefCell<Vec<Arc<FileSystemThing>>>,
    },
    File {
        name: String,
        size: usize,
    },
}
```

The two interesting bits to deal with are: 

* The `Arc` (atomic reference counter) wrappings on all `FileSystemThing`s. That's because I'm going to be using `clone` a bunch to attach those same references to a single file system thing to different parts in the tree. Specifically, the parents of each child and the child nodes themselves. 

* The `RefCell` in a directory's children. This came about because I need to be able to `mut` the children to `push` to it. I can't otherwise figure out how that's going to work. I kept getting this error:

    ```text
    error[E0596]: cannot borrow `*children` as mutable, as it is behind a `&` reference
    --> src/bin/07-recursive-fileinator.rs:95:25
    |
    95 |                         children.push(child);
    |                         ^^^^^^^^^^^^^^^^^^^^ `children` is a `&` reference, so the data it refers to cannot be borrowed as mutable
    ```

    With the `RefCell` though, I can `borrow` or `borrow_mut` the value as I need. 

Okay, so we have the structure... how do we build it? Well, here's what I did:

```rust
impl FileSystemThing {
    // Build a file system thing from an iter of commands run (cd and ls)
    fn from<I>(mut iter: I) -> Arc<Self>
    where
        I: Iterator<Item = String>,
    {
        use FileSystemThing::*;

        // Build a special :ROOT: node to start with
        let root = Arc::new(Directory {
            name: String::from(":ROOT:"),
            parent: None,
            children: RefCell::new(Vec::new()),
        });

        // Keep track of where we currently are after cds
        let current = RefCell::new(root.clone());

        while let Some(next) = iter.next() {
            let mut parts = next.split_ascii_whitespace();

            if next.starts_with("$ cd") {
                // cd changes directory and has three cases:
                //  "/" goes to root
                //  ".." goes up one level
                //  anything else goes into the named child directory

                let path = String::from(parts.last().expect("cd must have a directory"));

                // Build the next node depending on what we're cding too ("/", "..", or a name)
                let next = match current.borrow().as_ref() {
                    Directory { parent, .. } => {
                        if path == ".." {
                            match parent {
                                Some(parent) => parent.clone(),
                                _ => panic!("must have parent set to .."),
                            }
                        } else if path == "/" {
                            root.clone()
                        } else if let Some(child) = current.borrow().get(path) {
                            child
                        } else {
                            current.borrow().clone()
                        }
                    }
                    _ => current.borrow().clone(),
                };
                current.replace(next);
            } else if next.starts_with("$ ls") {
                // Starting an LS, nothing to do on this line
            } else if next.starts_with("dir") {
                // If we see a line starting with dir we're in an ls, create the directory

                let name = parts.last().expect("directory in ls must have a name");

                // If the file/directory already exists, we ran ls twice, ignore this
                if let Some(_child) = current.borrow().get(String::from(name)) {
                    continue;
                }

                // Build the new child directory referencing current as the parent
                let child = Arc::new(Directory {
                    name: String::from(name),
                    parent: Some(current.borrow().clone()),
                    children: RefCell::new(Vec::new()),
                });

                // Add a reference to the new directory to current's children
                match current.borrow().as_ref() {
                    Directory { children, .. } => {
                        children.borrow_mut().push(child);
                    }
                    _ => panic!("somehow tried to ls a file"),
                }
            } else {
                // Otherwise, it's a line containing the size and name of a file
                let size = parts
                    .next()
                    .expect("must have size")
                    .parse::<usize>()
                    .expect("size must be a usize");
                let name = parts.next().expect("must have a name");

                // If the file/directory already exists, we ran ls twice, ignore this
                if let Some(_child) = current.borrow().get(String::from(name)) {
                    continue;
                }

                // Build the new file, doesn't need a parent at least
                let child = Arc::new(File {
                    name: String::from(name),
                    size,
                });

                // Add a reference to the new file to current's children
                match current.borrow().as_ref() {
                    Directory { children, .. } => {
                        children.borrow_mut().push(child);
                    }
                    _ => panic!("somehow tried to put a file into another file"),
                }
            }
        }

        root.clone()
    }
}
```

Like I said, there are an awful lot of `clone` around, but that's fine. All that's essentially doing is telling `Arc` that we want more reference for it to count. Cheap. 

To break down the code a bit:

* Create a special `:ROOT:` node with no parent, this is the only reason we have `Option` on that...
* Set the `current` node to a `RefCell` of that, so we can update the reference 
* For each line in the input:
  * If it's a `cd`:
    * If it's `cd /`, change the `current` to the `:ROOT:` node; I don't think this actually happens
    * If it's `cd ..`, change to the parent directory of `current`; `panic` if we're at the root
    * If it's `cd $name`, change to that directory; assume that it's been 'created' / revealed by a previous `ls` (see below)
  * If it's an `ls`: we don't actually care, assume that all input not starting with `$` is part of an `ls`
  * If it's `dir $name`, create a new directory with `$name` and no children and attach it to `current` by:
    * Adding the new directory to `current.children` (with all the requisite indirection)
    * Set the `parent` of the new node to `current` (likewise)
  * If it's `$size $filename`, create a file, add it to `current.children`, and store the size with it

Ooo-kay. That took a while to get working. I think I have a better handle for what Rust needs to make these complicated `structs` work, but ... oh my is it a lot. 

It took ... a while to get to this. If you happen to be reading this and know of a more idiomatic / cleaner way to write the `from` code, I'd love to hear it. 

Okay, next we need the ability to recursively calculate the size at any given node:

```rust
impl FileSystemThing {
    // Get the size for a file or directory
    // Files directly have sizes, directories recursively sum their children's sizes
    pub fn size(&self) -> usize {
        use FileSystemThing::*;

        match self {
            Directory { children, .. } => {
                return children
                    .borrow()
                    .iter()
                    .map(|child| child.as_ref().size())
                    .sum()
            }
            File { size, .. } => *size,
        }
    }
}
```

That's not so bad. If it's a file, just return the size. If it's a directory, it doesn't have a size of it's own, so instead, borrow the children `RefCell`, `iter` through it, `map` each `child` to get the `size` (by calling this function, don't assume it's a file), and `sum`ing those. Clean, at least in my opinion. 

Okay, so we can build the tree and calculate the size at any point... but how do we go through and 'iterate' (as it were) over all of the nodes to find the ones that match our criteria? 

Okay, this one was also kind of a pain. This time, so that I can store the state of the iterator, I made a second struct `FileSystemIterator` and had `FileSystemThing` build one of those:

```rust
impl FileSystemThing {
    // Return an iterator over all nodes in the tree
    pub fn walk(&self) -> FileSystemIterator {
        FileSystemIterator::new(Arc::new(self.clone()))
    }
}
```

How I want to deal with this iterator is:

* Initialize a stack of `FileSystemThing` with the root node we're walking from
* Whenever `next` is called:
  * If the stack is empty: we're done, return `None` (stop iteration, I like doing it this way)
  * Otherwise, pop that thing off the stack and save it to return, but first:
    * For each child node of that thing, add it to the stack in our `Iterator` state
    * Now, return the popped node

```rust
// Iterate recursively over file systems
// Keep a stack of the children we've seen but not returned so far
struct FileSystemIterator {
    stack: Vec<Arc<FileSystemThing>>,
}

impl FileSystemIterator {
    fn new(root: Arc<FileSystemThing>) -> Self {
        FileSystemIterator { stack: vec![root] }
    }
}

impl Iterator for FileSystemIterator {
    type Item = Arc<FileSystemThing>;

    fn next(&mut self) -> Option<Self::Item> {
        use FileSystemThing::*;

        if self.stack.is_empty() {
            return None;
        }

        let next = self.stack.pop().unwrap();
        if let Directory { children, .. } = next.borrow() {
            for child in children.borrow().iter() {
                self.stack.push(child.clone());
            }
        }

        Some(next)
    }
}
```

Getting the right combination of references in this took a bit too... eventually I fell back again on `Arc`. It's ... actually the right tool for the job, no? Because I'll have at least two references kicking around at times, in children (and sometimes parents) and in the stack. 

Neat. 

Also note: because we're not reversing here, nodes at the same level will be returned in the opposite order they were seen on the input, you can add a `.rev()` at the end of the `children.borrow().iter()` line. But for these problems, it doesn't matter. 

Okay. So, what was the problem even? 

Right, iterate through the tree and sum up the recursive side (including overlaps) of all directories that have a size of no more than 100,000.

```rust
fn part1(filename: &Path) -> String {
    let root = FileSystemThing::from(iter_lines(filename));

    let mut total_sizes = 0;
    for node in root.walk() {
        match node.borrow() {
            FileSystemThing::Directory { .. } => {
                let size = node.size();
                if size <= 100000 {
                    total_sizes += size;
                }
            }
            _ => {}
        }
    }

    total_sizes.to_string()
}
```

Not so bad. 

One thing probably worth mentioning is that I implemented (and used here) an `iter_lines` method. It's the same as `from_lines`, it just doesn't `collect`, making it lazy for free. It doesn't matter at all in this case, but would 1) save some memory by not loading an entire file into memory and 2) allow you to partially consume the input easily. 

I may go back and change previous days over to this model. 

## Part 2

> Assume this virtual disk has total available space of `70,000,000`. You need `30,000,000` free. Find the smallest directory (recursively) you can delete that would leave you with `30,000,000` free and return it's size. 

I definitely made this more verbose than I needed to calculate this target. So it goes. 

Essentially, I want to:

* Calculate what the `target_to_free` size is
* Initialize how much is `freeable` to `usize::MAX` (since we want a minimum)
* Walk the file system
  * Skip files
  * For directories:
    * If it's larger than `target_to_free` and smaller than `freeable`, update `freeable`
    * Otherwise, skip it
* Return the final `freeable` value

```rust
fn part2(filename: &Path) -> String {
    let root = FileSystemThing::from(iter_lines(filename));

    let total_disk = 70000000;
    let needed = 30000000;
    let used = root.size();
    let available = total_disk - used;
    let target_to_free = needed - available;

    // We need the smallest directory at least larger than target_to_free
    let mut freeable = usize::MAX;

    for node in root.walk() {
        match node.borrow() {
            FileSystemThing::Directory { .. } => {
                let size = node.size();
                if size > target_to_free && size < freeable {
                    freeable = size;
                }
            }
            _ => {}
        }
    }

    freeable.to_string()
}
```

I do enjoy the programs where the final wrapper for part 2 is mostly done by properly engineering part 1. :smile:

## Performance

Fast:

```rust
./target/release/07-recursive-fileinator 1 data/07.txt

1453349
took 403.291µs
./target/release/07-recursive-fileinator 2 data/07.txt

2948823
took 421.666µs
```

Yeah... I don't really need to optimize that from a speed perspective. 

Like I said though, If you happen to be reading this and know of a more idiomatic / cleaner way to write the `from` code, I'd love to hear it. 