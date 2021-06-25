---
title: A Generic Brute Force Backtracking Solver
date: 2021-06-25
programming/languages:
- JavaScript
programming/topics:
- Small Scripts
programming/sources:
- Algorithms
- Backtracking
- Generators
- Puzzles
- Sudoku
---
One of the projects I've had vaguely in the back of my head is a sort of generic puzzle solver. I really love puzzles, but of the pencil and paper and video game varieties. So I think it would be awesome to write out a definition of a puzzle (say how to play Sudoku), give it input, and have it give me an answer back. 

Well, I finally got around to trying it!

<!--more-->

And it turns out for what I'm working on, it's actually not at all complicated code:

```javascript
export function makeSimpleSolver({
        generateNextStates,
        isValid,
        isSolved,
    }) {
    return (state) => {
        let visited = 0

        let recur = () => {
            visited++

            if (!isValid(state)) {
                return false
            }

            if (isSolved(state)) {
                return true
            }

            for (let {step, unstep} of generateNextStates(state)) {
                step(state)

                if (recur()) {
                    return true
                } else {
                    unstep(state)
                }
            }

            return false
        }
        recur()

        return state
    }
}
```

Essentially for any puzzle you want to solve, I want you to define three functions:

- `generateNextStates`: takes in the current 'state' (whatever that is) and returns an interable objects containing two functions {`step`, `unstep`}: 
    - `step`: Take the current state and make one move (move a piece in chess, fill in a number in a Sudoku puzzle)
    - `unstep`: Should be the exact inverse of the previous function
- `isValid`: Take a state and tell us if it's a valid state (this may be useless if the generator functions only return valid states, but I needed it for sudoku)
- `isSolved`: Return `true` if we have solved the problem

I'll admit the `generateNextStates` was particularly weird. If I was working with purely functional languages / immutable data structures, I would probably just keep the state that way. But working on a mutable state (with an undo function) lets us only keep one copy of the actual state data rather than copying it. 

It's like keeping only the current state of a chess board in memory and keeping a list of moves rather than keeping a copy of each possible chess board along the way. It should be somewhat more memory efficient. 

And that's all we need. Other than that, it's a standard recursive backtracker:

- Take the current state:
    - If it's an invalid state, ignore it
    - If it's a solved state, return it all the way back up the call stack
    - Otherwise, generate a list of moves, for each in turn:
        - Try to make that move and recursively solve from that point
        - If any branch of that state is a solution, keep returning 
        - If no state was, backtrack (undoing this step) and try another branch

Now, let's go back to my working example, a Sudoku solver. 

First, what are we using as the `state` of this problem. In this case, a 2D array where each value is 0-9. 1-9 are numbers and 0 is a blank space. 

Next, my 'moves' are going to be: find the first empty spaces and try every value in it. I'm not at all making sure that a particular number can be used in a space, that's what `isValid` is used for. 

After that, `isValid` and `isSolved` each basically require the same set of helper functions. One each to get all of the values in a specific row (`getRow`), column, or cell/block (the 3x3 subsections of the puzzle). The first two are straight forward, just access that `row` or `column` in the `state`, but the third is... weird. I mostly had to work it out, but it's a lot of modular math that gets the blocks from top left, across, and then down. 

After that, a quick functional way of determining if a list has any non-zero duplicates:

```javascript
let hasDup = (vs) => vs.some(v1 => v1 != 0 && vs.filter(v2 => v1 == v2).length != 1)
```

I'm actually quite happy with that function. It takes a list of values `vs` and asks if there is `some` value `v1` such that if you filter the list for only values `v2` that are the same as `v1` there's more than one of them (a duplicate!). I still really like functional programming, but the absolutely crazy number of libraries for JavaScript available is something to appreciate. Plus, I can run it directly in the browser!

So, putting this all together:

```javascript
import { makeSimpleSolver } from './solver.js'

let indexes = [0, 1, 2, 3, 4, 5, 6, 7, 8]

let getRow = (state, row) => indexes.map(i => state[row][i])
let getCol = (state, col) => indexes.map(i => state[i][col])
let getCel = (state, cel) => indexes.map(i => state[3 * Math.floor(cel / 3) + Math.floor(i / 3)][3 * (cel % 3) + (i % 3)])

let hasDup = (vs) => vs.some(v1 => v1 != 0 && vs.filter(v2 => v1 == v2).length != 1)

let solveSudoku = makeSimpleSolver({
    returnMeta: true,
    generateNextStates: function*(state) {
        // Find the first empty cell
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                if (state[i][j] == 0) {
                    // Try each value in it
                    for (let v = 1; v <= 9; v++) {
                        yield {
                            step: function(state) { state[i][j] = v },
                            unstep: function(state) { state[i][j] = 0 }
                        }
                    }
                    return
                }
            }
        }
    },
    isValid: function(state) {
        for (let p = 0; p < 9; p++) {
            if (hasDup(getRow(state, p)) 
                    || hasDup(getCol(state, p))
                    || hasDup(getCel(state, p)))
                return false
        }
        return true
    },
    isSolved: function(state) {
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                if (state[i][j] == 0)
                    return false
            }
        }

        for (let p = 0; p < 9; p++) {
            if (hasDup(getRow(state, p)) 
                    || hasDup(getCol(state, p))
                    || hasDup(getCel(state, p)))
                return false
        }

        return true
    }
})
```

And that's it! Let's run a few tests with some vague timing:

```javascript
import { sudokuToString, solveSudoku } from './sudoku.js'

let tests = {
    'easy': [
        [0,4,0,0,0,0,1,7,9],
        [0,0,2,0,0,8,0,5,4],
        [0,0,6,0,0,5,0,0,8],
        [0,8,0,0,7,0,9,1,0],
        [0,5,0,0,9,0,0,3,0],
        [0,1,9,0,6,0,0,4,0],
        [3,0,0,4,0,0,7,0,0],
        [5,7,0,1,0,0,2,0,0],
        [9,2,8,0,0,0,0,6,0]
    ],
    'hard': [
        [1,0,0,0,0,7,0,9,0],
        [0,3,0,0,2,0,0,0,8],
        [0,0,9,6,0,0,5,0,0],
        [0,0,5,3,0,0,9,0,0],
        [0,1,0,0,8,0,0,0,2],
        [6,0,0,0,0,4,0,0,0],
        [3,0,0,0,0,0,0,1,0],
        [0,4,0,0,0,0,0,0,7],
        [0,0,7,0,0,0,3,0,0]
    ],
    'hardest': [
        [8,0,0,0,0,0,0,0,0],
        [0,0,3,6,0,0,0,0,0],
        [0,7,0,0,9,0,2,0,0],
        [0,5,0,0,0,7,0,0,0],
        [0,0,0,0,4,5,7,0,0],
        [0,0,0,1,0,0,0,3,0],
        [0,0,1,0,0,0,0,6,8],
        [0,0,8,5,0,0,0,1,0],
        [0,9,0,0,0,0,4,0,0]
    ]
}

for (let test in tests) {
    let input = tests[test]

    console.log(`===== ${test} =====`)
    console.log(`input:`)
    console.log(sudokuToString(input))

    console.time(test)
    let output = solveSudoku(input)
    console.timeEnd(test)
    console.log()

    console.log(`output:`)
    console.log(sudokuToString(input))
}
```

Run:

```bash
===== easy =====
input:
040000179
002008054
006005008
080070910
050090030
019060040
300400700
570100200
928000060

easy: 46.848ms

output:
845632179
732918654
196745328
683574912
457291836
219863547
361429785
574186293
928357461

===== hard =====
input:
100007090
030020008
009600500
005300900
010080002
600004000
300000010
040000007
007000300

hard: 444.153ms

output:
162857493
534129678
789643521
475312986
913586742
628794135
356478219
241935867
897261354

===== hardest =====
input:
800000000
003600000
070090200
050007000
000045700
000100030
001000068
008500010
090000400

hardest: 2.034s

output:
812753649
943682175
675491283
154237896
369845721
287169534
521974368
438526917
796318452
```

Fun! And quick too. At least quick enough for what I'm looking for. 

Next up, I want to implement duplicate detection so that our solver doesn't get into infinite loops. This doesn't happen in Sudoku (since we're always adding elements, never removing them; other than backtacking). But in Chess for example, we could get in a state where we move the King back and forth indefiniately, which I want to avoid. 

And then... actual puzzle solvers!

Onward!
