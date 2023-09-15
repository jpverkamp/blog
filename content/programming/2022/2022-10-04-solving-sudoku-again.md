---
title: Solving Sudoku (again)
date: 2022-10-04
programming/languages:
- Rust
programming/topics:
- Algorithms
- Backtracking
- Generators
- Puzzles
- Sudoku
---
More [Rust](programming/languages/rust/)! This time, I want to go back to my post on [[A Generic Brute Force Backtracking Solver]](). For one, because I'm learning Rust. For two, because there is a crate specifically for {{<doc rust im>}}mutable data structures. And for three, because I expect it will be much faster. We shall see!

<!--more-->

## Representing the board

As one does, we're going to start with [[wiki:Sudoku]](). So to do that, we'll need to represent the board. Because it's just a 9x9 grid, I'm going to use Rust arrays:

```rust
#[derive(Copy, Clone, Debug)]
struct Sudoku {
    board: [[u8; 9]; 9]
}
```

And because I want a decent display function:

```rust
impl fmt::Display for Sudoku {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let mut s: String = String::new();
    
        s += "sudoku:\n";
        for x in 0..9 {
            s += "  ";
            for y in 0..9 {
                if self.board[x][y] == 0 {
                    s += " ";
                } else { 
                    // This seems weird
                    s = format!("{}{}", s, self.board[x][y]);
                }
                
                if y == 2 || y == 5 {
                    s += "|";
                }
            }
            s += "\n";
            
            if x == 2 || x == 5 {
                s += "  ---+---+---\n";
            }
        }
        
        write!(f, "{}", s)
    }
}
```

If there's a better way to do that... I'd love to here it. In particular, I couldn't figure out a better way to put in the `u8` to `String` bit without borrowing issues. Rust yo. 

So now I can create an initial board:

```rust
let initial_state = Sudoku { 
    board: [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0]
    ]
};
```

I'll use `0` for the empty spaces and the numbers for everything else. Cool. So next? 

## A `State` trait

Next, we need something to solve. The idea of defining a generic function in Rust that can operate over different sorts of problems fits perfectly into `trait`s, so let's make one:

```rust
pub trait State {
    fn next_states(self) -> Option<Vec<Self>> where Self: Sized + Copy;
    
    fn is_valid(self) -> bool;
    fn is_solved(self) -> bool;
}
```

For something to be a `State`, it needs to have three functions defined:

* `next_states` - takes a current state and returns `None` (if no new states can be generated) or `Some(Vec<State>)` that can be generated from that state
* `is_valid` - tells if a current state is valid (useful for some cases where I want `next_states` to generate too many, but I don't use it for Sudoku)
* `is_solved` - checks if this state is a solution, if so, we're done looking

So, let's implement those for Sudoku:

```rust
impl State for Sudoku {
    fn is_valid(self) -> bool {
        // TODO: Because we're always generating valid `next_states`
        //  this isn't necessary
        return true;
    }
    
    fn is_solved(self) -> bool {
        // TODO: Same as above, all states are `is_valid`
        //  so just check for no remaining empties
        for x in 0..9 {
            for y in 0..9 {
                if self.board[x][y] == 0 {
                    return false;
                }
            }
        }
        
        return true;
    }

    fn next_states(self) -> Option<Vec<Sudoku>> {
        let mut states = Vec::new();
        
        // Find the next empty square
        for x in 0..9 {
            for y in 0..9 {
                if self.board[x][y] == 0 {
                    // Try each value
                    'duplicate: for value in 1..=9 {
                        for other in 0..9 {
                            // Already used in this row or column, skip
                            if self.board[x][other] == value {
                                continue 'duplicate;
                            }
                            
                            if self.board[other][y] == value {
                                continue 'duplicate;
                            }
                            
                            // Already used in this 3x3 block, skip
                            if self.board[x / 3 * 3 + other / 3][y / 3 * 3 + other % 3] == value {
                                continue 'duplicate;
                            }
                        }

                        // Valid so far, so generate a new board using that value
                        let mut next = self.clone();
                        next.board[x][y] = value;
                        states.push(next);
                    }
                    
                    // Return the possible next states for this empty square
                    // If we didn't generate any states, something went wrong
                    if states.len() == 0 {
                        return None;
                    } else {
                        return Some(states);
                    }
                }
            }
        }
        
        // If we made it here, there are no empty squares, is_solved should be true
        // (We shouldn't make it here)
        None
    }
}
```

As I mentioned, we're just skipping `is_valid` and always returning `true`, since our `next_states` function explicitly only returns possible states. Likewise, `is_solved` just checks if there are any `0`s left, since we're assuming all states are valid. 

The interesting one is `next_states`. For this, we'll find the next open (`0`) spot on the board and try each of the 9 possible values. For each, check the row, column, and block it's in for any duplicates. If there are no duplicates, this will be a state we return. If there are any, skip this one and go on. If we get to the end of this check and none of the values fit into this empty square, this isn't a valid solution, so return `None` from `next_states`. The solver will know how to handle that. 

And that's all we need:

```rust
fn main() {
    let initial_state = Sudoku { 
        board: [
            [0, 0, 0, 2, 6, 0, 7, 0, 1],
            [6, 8, 0, 0, 7, 0, 0, 9, 0],
            [1, 9, 0, 0, 0, 4, 5, 0, 0],
            [8, 2, 0, 1, 0, 0, 0, 4, 0],
            [0, 0, 4, 6, 0, 2, 9, 0, 0],
            [0, 5, 0, 0, 0, 3, 0, 2, 8],
            [0, 0, 9, 3, 0, 0, 0, 7, 4],
            [0, 4, 0, 0, 5, 0, 0, 3, 6],
            [7, 0, 3, 0, 1, 8, 0, 0, 0]
        ]
    };
    println!("initial {}", initial_state);
    
    for state in initial_state.next_states().unwrap() {
        println!("potential {}", state);
    }
}

/* --- OUTPUT --- */
initial sudoku:
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

potential sudoku:
  3  |26 |7 1
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

potential sudoku:
  4  |26 |7 1
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

potential sudoku:
  5  |26 |7 1
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

```

If you go through it, `3`, `4`, and `5` are the possible top left states, so those are the ones it generated. In theory, you could optimize slightly by finding the most constrained squares and doing those first, but in practice, this works fine. 

Now, on to the actual solver!

## Solving the problem

For what it does, the state is pretty short:

```rust

fn solve<S>(initial_state: &S) -> Option<S> where S: State + Copy + std::fmt::Debug {
    let mut deq: VecDeque<S> = VecDeque::from([initial_state.clone()]);
    
    while !deq.is_empty() {
        let current_state = deq.pop_back().unwrap();
        
        if current_state.is_solved() {
            return Some(current_state);
        }
        
        // If we have next states, push those onto the queue
        // If not, just drop this state (and effectively backtrack)
        match current_state.next_states() {
            Some(ls) => {
                for next_state in ls {
                    if (next_state.is_valid()) {
                        deq.push_back(next_state);
                    }
                }
            },
            None => {}
        }
    }
    
    return None;
}
```

Initialize a {{<doc rust deque>}} (for the future when I want to support both depth and breadth first searches, a normal `Vec` would have worked for this) with the initial state then start iterating:

* For each state:
  * Check if it's solved, if so, return that as the answer
  * Otherwise, generate each of the possible `next_states`:
    * If that state is valid, add it to the queue
    * Otherwise, ignore it
  * Because the state is removed, if it has no possible child states, we will automatically backtrack here

Eventually, this will search the entire search space. Because it's a depth first search, it will go as far down each possible solution branch as it can until it either hits a dead end or finds the solution. 

Optimizations:

* Allow either depth or breadth first search
* Keep track of the steps we took to get to a specific state (possibly returning a `Vec` of tuples of `(Step, State)`)
* Keep track of how many states we evaluated to get to a specific point
* Don't examine duplicate states (we'll have to implement `Eq` for that)

Next time!

## Output time!

And of course it works (and fast), but let's take a quick look:

```rust
fn main() {
    let initial_state = Sudoku { 
        board: [
            [0,0,0,0,8,6,0,2,0],
            [0,0,6,4,0,0,0,0,0],
            [5,0,3,0,0,0,0,0,0],
            [0,0,4,6,0,0,7,0,8],
            [7,0,0,1,0,0,4,9,0],
            [0,0,0,3,0,0,5,0,0],
            [0,0,0,8,0,0,2,7,0],
            [6,0,0,2,0,3,1,5,0],
            [2,0,0,0,9,1,0,0,0],
        ]
    };
    println!("initial {}", initial_state);
    println!("solved {}", solve::<Sudoku>(&initial_state).unwrap());
}

/* --- OUTPUT --- */

initial sudoku:
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

solved sudoku:
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
```

Nice!