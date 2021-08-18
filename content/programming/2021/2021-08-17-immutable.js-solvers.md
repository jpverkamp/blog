---
title: Immutable.js Solvers
date: 2021-08-17
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
A bit ago I wrote about writing a [generic brute force solver]({{< ref "2021-06-25-a-generic-brute-force-solver" >}}) (wow, was that really two months ago?). It got ... complicate. Mostly, because every time I wrote a `step` function, I had to be careful to undo the same. Wouldn't it be nice if we could just write a step function and get backtracking for 'free'?

Well, with immutability you can! 

<!--more-->

It's something you see all of the time with functional languages, but it's less common in languages like JavaScript. In a nutshell, the idea is that once you create a datastructure, that structure will never change. If you want to (for example), add an element to a list, you instead create a new list which is defined as the old list with one more element. Something like this:

```javascript
// With a traditional list
> ls = [1, 2, 3]
> ls.push(4)
> console.log(ls)
[1, 2, 3, 4]

// With an immutable list
> ls = List([1, 2, 3])
> ls.push(4)
> console.log(ls.toJS())
[1, 2, 3]
> ls = ls.push(4)
> console.log(ls.toJS())
[1, 2, 3, 4]
```

Pretty cool! Note, the first time in the last example, `ls` didn't change. In the second example, it looks like it changed... but that's because we changed `ls` to point to the new list:

```javascript
> ls = List([1, 2, 3])
> ls2 = ls.push(4)
> console.log(ls)
[1, 2, 3]
> console.log(ls2)
[1, 2, 3, 4]
```

That gives you one huge advantage: If you add something to a list then try to solve a problem with that, any references to the original list aren't changed. So if that branch doesn't work out, you can just discard it and you still have the original list. There are a few performance downsides to doing it this way, but it's really quite nice. Let's make it work. 

Start with [immutable.js](https://github.com/immutable-js/immutable-js). 

```javascript
import { Map, List, Set, Record, fromJS } from 'immutable'

export function makeSolver({
        generateNextStates, // state -> [{state, step: String}, ...] // The string is a description of the step
        isValid,            // state -> Boolean: Is the given state valid
        isSolved,           // state -> Boolean: Is the given state a solution
    }) {

    // Takes a state and returns {state, steps, iterations}
    // If returnFirst is set, return the first solution we find; if not, keep looking and return the shortest solution
    return (state) => {
        let startTime = Date.now()

        // Each node stores a state, it's parent, and the step to get to it
        let Node = Record({
            state: null,
            previousNode: null,
            step: null,
        })

        // Visited is a map of state into the node graph
        let visited = Map()

        // Calculate the steps to get to a specific node
        let stepsTo = (node) => {
            let steps = []

            while (node) {
                steps.unshift(node.step)
                node = node.previousNode
            }

            return steps
        }

        // List of states to visit, paired with the steps taken to get to them
        // Starts with the initial state and no steps (since we just started here)
        let toVisit = List().push(Node({
            state: fromJS(state),
            step: 'start'
        }))
        
        // Count how many nodes we processed for logging purposes
        let iterations = 0

        // As long as we have at least one more node to visit, keep going
        while (toVisit.size > 0) {
            iterations++
            if (iterations % 1000 == 0) console.log(`iteration: ${iterations}, queue size: ${toVisit.size}`)

            // Pop off the new value we're working on
            let currentNode = toVisit.first()
            let {state: currentState, previousNode, step} = currentNode
            toVisit = toVisit.shift()

            // If this state is invalid, discard it and move on
            if (!isValid(currentState)) {
                continue
            }

            // If we have a solution:
            // - If we're returning the first solution, return it and steps to get to it
            // - If not, record it
            if (isSolved(currentState)) {
                return {
                    state: currentState.toJS(),
                    steps: stepsTo(currentNode),
                    iterations,
                    duration: (Date.now() - startTime) / 1000
                }
            }

            // Otherwise, check if we've reached a new known state
            if (visited.has(currentState)) {
                continue
            } else {
                visited = visited.set(currentState, currentNode)                
            }

            // A valid state that isn't a solution, check all neighbors from this state
            for (let {state: nextState, step} of generateNextStates(currentState)) {
                let newNode = Node({
                    state: nextState,
                    previousNode: currentNode,
                    step: step
                })

                // Depth first search adds to the beginning (search these before all current nodes)
                toVisit = toVisit.unshift(newNode)
            }
        }
    }
}
```

And that's actually it. It's pretty close to [last time]({{< ref "2021-06-25-a-generic-brute-force-solver" >}}). We do have to tweak our Sudoku solver to use immutable data structures a bit to use all of this information, but only a few tweaks (mostly in the `yield` of `generateNextStates` and using `.get` instead of `[]` for indexing):

```javascript
import { Set } from 'immutable'
import { makeSolver } from './solvers/immutable.js'

let indexes = [0, 1, 2, 3, 4, 5, 6, 7, 8]

let getRow = (state, row) => indexes.map(i => state.get(row).get(i))
let getCol = (state, col) => indexes.map(i => state.get(i).get(col))
let getCel = (state, cel) => indexes.map(i => state.get(3 * Math.floor(cel / 3) + Math.floor(i / 3)).get(3 * (cel % 3) + (i % 3)))

let getCelIndex = (r, c) => Math.floor(r / 3) * 3 + Math.floor(c / 3)

let hasDup = (vs) => vs.some(v1 => v1 != 0 && vs.filter(v2 => v1 == v2).length != 1)

let generateNextStates = function*(state) {
    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            if (state.get(i).get(j) === 0) {
                for (let v = 1; v <= 9; v++) {
                    yield {
                        state: state.set(i, state.get(i).set(j, v)),
                        step: `(${i}, ${j}) => ${v}`
                    }
                }
                return
            }
        }
    }
}

let isValid = function(state) {
    for (let p = 0; p < 9; p++) {
        if (hasDup(getRow(state, p)) 
                || hasDup(getCol(state, p))
                || hasDup(getCel(state, p)))
            return false
    }
    return true
}

let isSolved = function(state) {
    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            if (state.get(i).get(j) === 0)
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

let solveSudoku = makeSolver({
    generateNextStates,
    isValid,
    isSolved,
    returnFirst: true,
    debug: false,
    searchMode: 'dfs', 
})

let sudokuToString = (state) => state.map(row => row.join('')).join('\n') + '\n'

export { solveSudoku, sudokuToString }
```

Pretty cool. Let's try it:

```javascript
> import('./sudoku.js').then(({ solveSudoku, sudokuToString }) => {
...     let input = [
...         [0,4,0,0,0,0,1,7,9],
...         [0,0,2,0,0,8,0,5,4],
...         [0,0,6,0,0,5,0,0,8],
...         [0,8,0,0,7,0,9,1,0],
...         [0,5,0,0,9,0,0,3,0],
...         [0,1,9,0,6,0,0,4,0],
...         [3,0,0,4,0,0,7,0,0],
...         [5,7,0,1,0,0,2,0,0],
...         [9,2,8,0,0,0,0,6,0]
...     ]
... 
...     let {state, steps, iterations, duration} = solveSudoku(input)
...     
...     console.log(`solved in ${iterations} iterations over ${duration} seconds`)
...     console.log(sudokuToString(state))
... })

solved in 485 iterations over 0.02 seconds
845632179
732918654
196745328
683574912
457291836
219863547
361429785
574186293
928357461
```

Nice. Now that we have a solver, let's see just how crazy we can get with more options. For example, different search modes:

* Breadth first search (check all possibilities of 1 step, then 2, etc)
* Depth first search (go all the way down one branch before backtracking along the next)
* Score best searching (assign a score to each state, work on the highest ones first)

To do this, we add a `searchMode` parameter and then add in a few different cases for how we queue up new cases to check. I think the best part is that it's actually simple code. If we're searching depth first, we add new nodes to the same side of the list we're taking from. Breadth first search adds to the opposite end. The more complicated one is scoring based. But since we're controlling the order of the list, we can do a binary insertion and still be efficient (`log(n)` on the number of current nodes). 

Nice!

```javascript
...
let newNode = Node({
    state: nextState,
    previousNode: currentNode,
    step: step,
    distance: distance + 1,
})

// Depth first search adds to the beginning (search these before all current nodes)
if (searchMode === 'dfs' || searchMode === undefined) {
    toVisit = toVisit.unshift(newNode)
}

// Breadth first search adds to the end (so we'll search these after all current nodes)
else if (searchMode == 'bfs') {
    toVisit = toVisit.push(newNode)
}

// Functional search, calculates and includes a score
// toVisit will be sorted by these scores descending
// Highest scores will end up at the beginning of the list, so will be processed first
// If score returns a constant score, this is equivalent to DFS
else if (typeof (searchMode) === 'function') {
    // Calculate the score for the next state
    newNode = newNode.set('score', searchMode(nextState))

    if (debug) console.log(`scored new node ${newNode.score}: ${newNode.state}`)

    // Edge case, no nodes
    if (toVisit.size === 0) {
        toVisit = toVisit.push(newNode)
        continue
    }

    // Use a binary search to insert the scored node into the visited nodes
    let lo = 0
    let hi = toVisit.size - 1
    while (hi - lo > 1) {
        let mid = ((lo + hi) / 2) | 0 // Integer division by forcing cast to Int for | operator

        if (newNode.score >= toVisit.get(mid).score) {
            hi = mid
        } else {
            lo = mid
        }
    }
    toVisit = toVisit.insert(lo, newNode)
}
...
```

While we're at it, let's add an ability to bail out early as well at the end of the same loop:

```javascript
// If we've spent too long, bail out
let currentDuration = (Date.now() - startTime) / 1000
if (maxTime !== undefined && currentDuration > maxTime) {
    error = 'maxTime reached'
    break
}
```

Another way we can tweak this search would be to try different move generators. For the case of Sudoku, we're doing the most brute force solution of all right now where were' starting in the top left and moving across, but we don't have to. Instead, let's start with the 'fewest degrees of freedom': those squares in the Sudoku that only have one or two options before those that can still be any number:


```javascript
let generateNextStates = function*(state) {
    // Find the empty cell with the fewest degrees of freedom
    let bestI = 0
    let bestJ = 0
    let bestDoF = 100
    let bestVS = null

    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            if (state.get(i).get(j) === 0) {
                let row = Set(getRow(state, i))
                let col = Set(getCol(state, j))
                let cel = Set(getCel(state, getCelIndex(i, j)))
                let all = row.union(col).union(cel)
                let dof = 10 - all.size

                if (bestVS === null || dof < bestDoF) {
                    bestI = i
                    bestJ = j
                    bestDoF = dof
                    bestVS = Set([1, 2, 3, 4, 5, 6, 7, 8, 9]).subtract(all)
                }
            }
        }
    }

    for (let v of bestVS) {
        yield {
            state: state.set(bestI, state.get(bestI).set(bestJ, v)),
            step: `(${bestI}, ${bestJ}) => ${v}`
        }
    }
}
```

A little bit more complicated, but it's also much faster. Here are some tests with all of the given search methods (constant score always returns 1, it defaults to DFS; count DOF is like using the better generator). Try this on three problems of increasing difficulty and what do you have?

| Search Name              | Generator Name                       | Test Name | Iterations | Duration | Iter/Sec | Error           |
| ------------------------ | ------------------------------------ | --------- | ---------- | -------- | -------- | --------------- |
| Depth First Search       | Fill from top left                   | easy      | 485        | 0.02     | 24250    |                 |
| Depth First Search       | Fill from top left                   | hard      | 89524      | 3.588    | 24951    |                 |
| Depth First Search       | Fill from top left                   | hardest   | 240205     | 30.004   | 8006     | maxTime reached |
| Breadth First Search     | Fill from top left                   | easy      | 4754       | 0.036    | 132056   |                 |
| Breadth First Search     | Fill from top left                   | hard      | 169952     | 16.288   | 10434    |                 |
| Breadth First Search     | Fill from top left                   | hardest   | 69729      | 30.005   | 2324     | maxTime reached |
| Constant score           | Fill from top left                   | easy      | 485        | 0.022    | 22045    |                 |
| Constant score           | Fill from top left                   | hard      | 89524      | 4.145    | 21598    |                 |
| Constant score           | Fill from top left                   | hardest   | 225732     | 30.003   | 7524     | maxTime reached |
| Count non-zero squares   | Fill from top left                   | easy      | 485        | 0.012    | 40417    |                 |
| Count non-zero squares   | Fill from top left                   | hard      | 89524      | 4.047    | 22121    |                 |
| Count non-zero squares   | Fill from top left                   | hardest   | 228758     | 30.004   | 7624     | maxTime reached |
| Count degrees of freedom | Fill from top left                   | easy      | 3529       | 0.255    | 13839    |                 |
| Count degrees of freedom | Fill from top left                   | hard      | 77975      | 8.288    | 9408     |                 |
| Count degrees of freedom | Fill from top left                   | hardest   | 48649      | 30.009   | 1621     | maxTime reached |
| Depth First Search       | Fill fewest degrees of freedom first | easy      | 49         | 0.013    | 3769     |                 |
| Depth First Search       | Fill fewest degrees of freedom first | hard      | 2073       | 0.445    | 4658     |                 |
| Depth First Search       | Fill fewest degrees of freedom first | hardest   | 8895       | 4.192    | 2122     |                 |
| Breadth First Search     | Fill fewest degrees of freedom first | easy      | 49         | 0.005    | 9800     |                 |
| Breadth First Search     | Fill fewest degrees of freedom first | hard      | 2232       | 0.448    | 4982     |                 |
| Breadth First Search     | Fill fewest degrees of freedom first | hardest   | 18936      | 18.768   | 1009     |                 |
| Constant score           | Fill fewest degrees of freedom first | easy      | 49         | 0.005    | 9800     |                 |
| Constant score           | Fill fewest degrees of freedom first | hard      | 2073       | 0.367    | 5649     |                 |
| Constant score           | Fill fewest degrees of freedom first | hardest   | 8895       | 3.855    | 2307     |                 |
| Count non-zero squares   | Fill fewest degrees of freedom first | easy      | 49         | 0.005    | 9800     |                 |
| Count non-zero squares   | Fill fewest degrees of freedom first | hard      | 2073       | 0.377    | 5499     |                 |
| Count non-zero squares   | Fill fewest degrees of freedom first | hardest   | 8895       | 3.707    | 2400     |                 |
| Count degrees of freedom | Fill fewest degrees of freedom first | easy      | 49         | 0.022    | 2227     |                 |
| Count degrees of freedom | Fill fewest degrees of freedom first | hard      | 2090       | 1.111    | 1881     |                 |
| Count degrees of freedom | Fill fewest degrees of freedom first | hardest   | 9183       | 7.246    | 1267     |                 |

That's pretty cool. The better generator really makes a huge difference, changing the fill from the top left to fill fewest degrees of freedom gives actually makes the hardest problem solveable in a few seconds rather than more than 30 on my machine. Check `iterations`, this is because you only have to check some 10,000 states before you find an answer, rather than half a million or more. 

That's even the case although we are definitely spending more time. The iterations/second is much higher, but it's worth the cost.  

On top of that, there are a few other changes. For example, depth first search is better than breadth first for this case for the same reason (500 versus 5000 iterations on harder problems, solving with almost no backtracking and only 50 iterations on the easiest).

There are still a few more tweaks that I want to do. In particular, I want to update the code that we can find the best solution rather than just the first one. To do that, we can use my `visisted` structure with one big tweak: when we go to a node we've seen before, if we've found a better path to it, store that. If we find a solution, mark down that node. At the end, search all solution nodes, and return the best. 

But that can wait a day or two. 

Until then, current source:

* [sudoku.js](https://github.com/jpverkamp/solvers/blob/main/sudoku.js)
* [solvers/immutable.js](https://github.com/jpverkamp/solvers/blob/main/solvers/immutable.js)


<script src="https://unpkg.com/sorttable@1.0.2/sorttable.js"></script>
<script>Array.from(document.querySelectorAll('table')).forEach((el) => el.classList.add('sortable'))</script>