---
title: Stateful Solvers and Iterators
date: 2022-10-16
programming/languages:
- Rust
programming/topics:
- Algorithms
- Backtracking
- Generators
- Puzzles
- Sudoku
series:
- Rust Solvers
---
[Rust](programming/languages/rust/), yet again! Let's take what we did last time with [[Solving Sudoku (again)]]() and improve the code structure a bit more. 

Goals:

* Create a 'Solver' struct that can maintain state (such as how many states we've visited, how much time we've spent)
* Track the above stats
* Turn the 'Solver' into an iterator which will iterate through given solutions (a single call will give the first solution or you can run through the iterator to get all of them)

If you'd like to follow along, I've started uploading the code here: https://github.com/jpverkamp/rust-solvers

<!--more-->

## The `Solver` 

```rust
#[derive(Debug)]
pub enum SearchMode {
    BreadthFirst,
    DepthFirst,
}

#[derive(Debug)]
pub struct Solver<S: State> {
    to_check: VecDeque<S>,
    checked: HashSet<S>,
    search_mode: SearchMode,
    time_spent: f32,
}
```

Okay, first up, let's store the data in the `Solver` that we'll use for any solution. The same `to_check` and `checked` objects from the previous solver (length of `checked` will be the number of states we've visited), the mode we're searching in (can add more later), and time spent. 

Next, constructors: 

```rust
impl<S> Solver<S> where S: State + Copy {
    pub fn new(initial_state: &S) -> Solver<S> {
        Solver {
            to_check: VecDeque::from([initial_state.clone()]),
            checked: HashSet::new(),
            search_mode: SearchMode::DepthFirst,
            time_spent: 0 as f32,
        }
    }

    pub fn set_mode(&mut self, new_mode: SearchMode) {
        self.search_mode = new_mode;
    }

    pub fn states_checked(&self) -> usize {
        self.checked.len()
    }

    pub fn time_spent(&self) -> f32 {
        self.time_spent
    }
}
```

Sometimes, I wish that Rust allowed function overloading a la Java, so that you can provide defaults to parameters more easily. I do like that it's explicit sometimes though. And hey, chaining with `set_mode` works well enough. 

## Implementing `Iterator`

Next up, let's implement `Iterator`. This let's us do awesome things like `for` loops, `.next()` and `.iter()` etc. 

Specifically, I'm going to take the current state and run through the search until we find the next valid state. This is the previous solve function, just wrapped up in the iterator syntax. 

```rust
// Iterate through the solver's given solutions until all are returned
impl<S> Iterator for Solver<S> where S: State + Copy {
    type Item = S;

    fn next(&mut self) -> Option<Self::Item> {
        let start = Instant::now();

        while !self.to_check.is_empty() {
            let current_state = match self.search_mode {
                SearchMode::BreadthFirst => self.to_check.pop_front().unwrap(),
                SearchMode::DepthFirst => self.to_check.pop_back().unwrap()
            };
            self.checked.insert(current_state);
            
            // If this is a valid solution, return it from our iterator
            if current_state.is_solved() {
                self.time_spent += start.elapsed().as_secs_f32();
                return Some(current_state);
            }
            
            // Otherwise:
            // - If we have next states, push those onto the queue
            // - If not, just drop this state (and effectively backtrack)
            if let Some(ls) = current_state.next_states() {
                for next_state in ls {
                    if self.checked.contains(&next_state) { continue; }
                    if !next_state.is_valid() { continue; }
        
                    self.to_check.push_back(next_state);
                }
            }
        }

        // If we make it here, return None to stop iterator
        self.time_spent += start.elapsed().as_secs_f32();
        return None;
    }

}
```

This actually seems really clean. I did add the `Instant.now()` so that any time spent working on solving the problem is recorded. But otherwise, it's the same function.

## A new `bin/sudoku.rs` binary

As another fun bit, I'm actually going to be moving the solver into it's own binary. If I put it in `src/bin/sudoku.rs`, when I build the project I get `./sudoku`, which is pretty cool!

Specifically, I'm going to make that binary load a Sudoku puzzle from a file and solve it several ways with timing:

```rust
fn main() {
    env_logger::init();

    let mut board = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ];
    
    for (i, line) in io::stdin().lock().lines().enumerate() {
        for (j, c) in line.unwrap().as_bytes().iter().enumerate() {
            board[i][j] = c - b'0';
        }
    }

    let initial_state = Sudoku { board };
    println!("initial: {}", initial_state);
    
    {
        println!("\nBreadth first:");
        let mut solver = Solver::new(&initial_state);
        solver.set_mode(SearchMode::BreadthFirst);
        match solver.next() {
            Some(solution) => println!("solution: {}", solution),
            None => println!("no solution found! :(")
        };
        println!("{} states, {} seconds", solver.states_checked(), solver.time_spent());
    }

    {
        println!("\nDepth first:");
        let mut solver = Solver::new(&initial_state);
        solver.set_mode(SearchMode::DepthFirst);
        match solver.next() {
            Some(solution) => println!("solution: {}", solution),
            None => println!("no solution found! :(")
        };
        println!("{} states, {} seconds", solver.states_checked(), solver.time_spent());
    }

    {
        println!("\nCheck all (loop):");
        let mut solver = Solver::new(&initial_state);
        
        loop {
            match solver.next() {
                Some(solution) => println!("solution: {}", solution),
                None => { break; }
            };
        }

        println!("{} states, {} seconds", solver.states_checked(), solver.time_spent());
    }

    {
        println!("\nCheck all (for):");
        let mut solver = Solver::new(&initial_state);
        
        for solution in &mut solver {
            println!("solution: {}", solution);
        }

        println!("{} states, {} seconds", solver.states_checked(), solver.time_spent());
    }    
}
```

I think that's pretty cool!

One interesting thing that I had to deal with was eventually getting the `for` loop working. For the longest time, I could use `for`, but then the borrow checker got made when I tried to get the default information back out at the end, since the `for` loop would take ownership.

Manually managing it with `loop` worked fine, but not `for`, since it uses `into_iter` (as far as I understand). But I did get it working eventually... just add an `&mut` to explicitly mutably reference the solver. Still getting used to that. 

## Testing and timing

Using a few random puzzles I found on the internet ([easy](https://github.com/jpverkamp/rust-solvers/blob/main/data/sudoku/easy.txt), [hard](https://github.com/jpverkamp/rust-solvers/blob/main/data/sudoku/hard.txt), and [evil](https://github.com/jpverkamp/rust-solvers/blob/main/data/sudoku/evil.txt)): 

### `easy`

```text
$ cat data/sudoku/easy.txt | ./target/release/sudoku

initial: sudoku <
     |26 |7 1
  68 | 7 | 9
  19 |  4|5
  ---+---+---
  82 |1  | 4
    4|6 2|9
   5 |  3| 28
  ---+---+---
    9|3  | 74
   4 | 5 | 36
  7 3| 18|
>

Breadth first:
solution: sudoku <
  435|269|781
  682|571|493
  197|834|562
  ---+---+---
  826|195|347
  374|682|915
  951|743|628
  ---+---+---
  519|326|874
  248|957|136
  763|418|259
>
69 states, 0.000126291 seconds

Depth first:
solution: sudoku <
  435|269|781
  682|571|493
  197|834|562
  ---+---+---
  826|195|347
  374|682|915
  951|743|628
  ---+---+---
  519|326|874
  248|957|136
  763|418|259
>
60 states, 0.000105416 seconds

Check all (loop):
solution: sudoku <
  435|269|781
  682|571|493
  197|834|562
  ---+---+---
  826|195|347
  374|682|915
  951|743|628
  ---+---+---
  519|326|874
  248|957|136
  763|418|259
>
69 states, 0.000111166 seconds

Check all (for):
solution: sudoku <
  435|269|781
  682|571|493
  197|834|562
  ---+---+---
  826|195|347
  374|682|915
  951|743|628
  ---+---+---
  519|326|874
  248|957|136
  763|418|259
>
69 states, 0.000109541004 seconds
```

### `hard`

```text
cat data/sudoku/hard.txt | ./target/release/sudoku

initial: sudoku <
  385|   |
    1|  9|
    2| 61|
  ---+---+---
   2 | 5 |  8
     | 3 |
     |1  | 35
  ---+---+---
     |7 4|6
  8  |   |2
   7 |   | 1
>

Breadth first:
solution: sudoku <
  385|247|961
  761|589|342
  942|361|857
  ---+---+---
  123|456|798
  457|938|126
  698|172|435
  ---+---+---
  519|724|683
  834|615|279
  276|893|514
>
165994 states, 0.11690296 seconds

Depth first:
solution: sudoku <
  385|247|961
  761|589|342
  942|361|857
  ---+---+---
  123|456|798
  457|938|126
  698|172|435
  ---+---+---
  519|724|683
  834|615|279
  276|893|514
>
113892 states, 0.053865753 seconds

Check all (loop):
solution: sudoku <
  385|247|961
  761|589|342
  942|361|857
  ---+---+---
  123|456|798
  457|938|126
  698|172|435
  ---+---+---
  519|724|683
  834|615|279
  276|893|514
>
165994 states, 0.088472456 seconds

Check all (for):
solution: sudoku <
  385|247|961
  761|589|342
  942|361|857
  ---+---+---
  123|456|798
  457|938|126
  698|172|435
  ---+---+---
  519|724|683
  834|615|279
  276|893|514
>
165994 states, 0.09432971 seconds
```

### `evil`

```text
cat data/sudoku/evil.txt | ./target/release/sudoku

initial: sudoku <
  3  |   | 2
  4  | 9 |
   92|6  |8
  ---+---+---
  9  |   |
   51| 6 | 4
     |8  |  7
  ---+---+---
     |  1|4
    3|   |
   26| 5 | 1
>

Breadth first:
solution: sudoku <
  365|178|924
  418|293|675
  792|645|831
  ---+---+---
  987|534|162
  251|967|348
  634|812|597
  ---+---+---
  579|321|486
  143|786|259
  826|459|713
>
1121590 states, 0.7149536 seconds

Depth first:
solution: sudoku <
  365|178|924
  418|293|675
  792|645|831
  ---+---+---
  987|534|162
  251|967|348
  634|812|597
  ---+---+---
  579|321|486
  143|786|259
  826|459|713
>
951510 states, 0.58878344 seconds

Check all (loop):
solution: sudoku <
  365|178|924
  418|293|675
  792|645|831
  ---+---+---
  987|534|162
  251|967|348
  634|812|597
  ---+---+---
  579|321|486
  143|786|259
  826|459|713
>
1121590 states, 0.6640801 seconds

Check all (for):
solution: sudoku <
  365|178|924
  418|293|675
  792|645|831
  ---+---+---
  987|534|162
  251|967|348
  634|812|597
  ---+---+---
  579|321|486
  143|786|259
  826|459|713
>
1121590 states, 0.69278765 seconds
```

## The advantages of release mode

Speaking of, there's one interesting thing to note. `--release` mode is *so much faster*:

```text
$ cargo build 
$ cat data/sudoku/evil.txt | ./target/debug/sudoku

...
1121590 states, 10.613164 seconds

$ cargo build --release
$ cat data/sudoku/evil.txt | ./target/release/sudoku

...
1121590 states, 0.69278765 seconds
```

Nice. 

## Next steps

A few possibilities:

* Implement different `nextStates` possibilities a la [[Immutable.js Solvers]]()
* Implement other puzzles a la [[Solving Snakebird]]()

Onward!