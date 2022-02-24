---
title: Solving Snakebird
date: 2021-08-18
programming/languages:
- JavaScript
programming/sources:
- Small Scripts
programming/topics:
- Algorithms
- Backtracking
- Generators
- Puzzles
---
[Snakebird!](https://store.steampowered.com/app/357300/Snakebird/)

{{< figure src="/embeds/2021/snakebird-0.png" >}}

A cute little puzzle game, where you move around snake(birds). Move any number of snakes around the level, eating fruit, and getting to the exit. The main gotchas are that you have gravity to content with--your snake will easily fall off the edge of the world--and each time you eat a fruit, your snake gets bigger. This can help get longer to get into hard to reach places or it can cause trouble when you trap yourself in corners. 

Let's use the new [immutable.js solver](2021-08-17-immutable.js-solvers) to solve these problems!

<!--more-->

First, a representation of state. The above level can be represented in a text format as so:

```text
----------------------
--------##-----*------
--------####----------
----#----##-----------
------#--#---+-#------
---CBA---#-#---##---+-
-#######---##-------##
######################
```

The snake is defined as `ABC` (you can currently have up to three, `A-Z`, `a-z`, and `0-9`). Walls are `#`, fruit is `+`, and the exit is `*`. Later levels have spikes that kill you on contact, which I'll represent with `^`.

To load that in, we scan through the lines/columns of that input, building up an immutable.js `Record` with a `Set` of `Point` (another `Record`) for each type of object. The snakes are `List` of `Point` (although once they leave, I will `null` them out). 

```javascript
import { List, Set, Record } from 'immutable'

const SNAKE_BOUNDS = [
    {min: 'A', max: 'Z'},
    {min: 'a', max: 'z'},
    {min: '0', max: '9'},
]

let Point = Record({r: 0, c: 0})
let State = Record({
    walls: Set(),   // tiles that can't be walked through
    spikes: Set(),  // tiles that kill snakes touching them
    snakes: List(), // each snake is an ordered list of points from head to tail
    fruits: Set(),  // each fruit makes the snake that eats it one longer
    exit: Point(),  // each snake that reaches the exit is removed, when the last is removed you win
})

function loadLevel(path) {
    let rawData = fs.readFileSync(path, {encoding: 'utf8'})
    let data = rawData.split('\n')

    let walls = Set()
    let spikes = Set()
    let snakes = List()
    let fruits = Set()
    let exit = Point()

    // a list of snake definitions in files with an ordered range of characters for each
    // example snakes would be ABC or abc or 123
    let rawSnakes = SNAKE_BOUNDS.map(_ => [])
    
    for (var r = 0; r < data.length; r++) {
        cloop:
        for (var c = 0; c < data[r].length; c++) {
            let pt = Point({r, c})

            // empty space
            if (data[r][c] == '-') {
                continue
            }
            
            // walls
            if (data[r][c] == '#') {
                walls = walls.add(pt)
                continue
            }

            // spikes
            if (data[r][c] == '^') {
                spikes = spikes.add(pt)
                continue
            }
            
            // fruits
            if (data[r][c] == '+') {
                fruits = fruits.add(pt)
                continue
            }
    
            // exit
            if (data[r][c] == '*') {
                exit = pt
                continue
            }
    
            // snakes, just collect the points for now with the character for later sorting
            for (let i = 0; i < SNAKE_BOUNDS.length; i++) {
                if (data[r][c] >= SNAKE_BOUNDS[i].min && data[r][c] <= SNAKE_BOUNDS[i].max) {
                    rawSnakes[i].push([data[r][c], pt])
                    continue cloop
                }
            }
    
            // wtf
            throw `Unknown character ${data[r][c]} at ${r}:${c}`
        }
    }

    // sort the snakes based on their character definition, push the list of points to state
    for (let rawSnake of rawSnakes) {
        if (rawSnake.length == 0) continue

        let pts = []
        for (let [_, pt] of rawSnake.sort()) {
            pts.push(pt)
        }
        snakes = snakes.push(List(pts))
    }

    return State({walls, spikes, snakes, fruits, exit})
}
```

Next, let's reverse that for debugging purposes:

```javascript
function snakebirdToString(state) {
    // Determine drawing bounds
    // This is necessary since snakes can run off platforms a bit
    let [minR, maxR, minC, maxC] = [0, 0, 0, 0]
    function bound(pt) {
        minR = Math.min(minR, pt.r)
        maxR = Math.max(maxR, pt.r)
        minC = Math.min(minC, pt.c)
        maxC = Math.max(maxC, pt.c)
    }
    
    state.walls.forEach(bound)
    state.snakes.forEach(snake => snake != null && snake.forEach(bound))
    state.fruits.forEach(bound)
    bound(state.exit)

    let str = ''
    for (let r = minR; r <= maxR; r++) {
        for (let c = minC; c <= maxC; c++) {
            let pt = Point({r, c})
            
            if (state.walls.has(pt)) {
                str += '#'
            } else if (state.spikes.has(pt)) {
                str += '^'
            } else if (state.fruits.has(pt)) {
                str += '+'
            } else if (state.exit.equals(pt)) {
                str += '*'
            } else if (state.snakes.some(snake => snake != null && snake.includes(pt))) {
                for (let i = 0; i < state.snakes.size; i++) {
                    if (state.snakes.get(i) == null) continue
                    for (let j = 0; j < state.snakes.get(i).size; j++) {
                        if (state.snakes.get(i).get(j).equals(pt)) {
                            str += String.fromCharCode(SNAKE_BOUNDS[i].min.charCodeAt(0) + j)
                        }
                    }
                }
            } else {
                str += '-'
            }
        }

        str += '\n'
    }

    return str
}
```

It will get confused if more than one type of object is in the same place, but that shouldn't be possible, so we'll ignore the possibility for now. 

Next, the `isValid` and `isSolved` functions, these are the easier part:

```javascript
let isValid = function (state) {
    // check if any snake is on a spike
    if (state.snakes.some(snake => snake != null && snake.some(pt => state.spikes.has(pt)))) return false

    // check if any snake is falling forever

    // find the lowest row
    let maxR = 0
    state.walls.forEach(pt => { maxR = Math.max(maxR, pt.r) })

    // check that each snake has at least one point within that bound
    return state.snakes.every(snake => snake == null || snake.some(pt => pt.r <= maxR))
}

let isSolved = function (state) {
    return state.fruits.size == 0 && state.snakes.every(snake => snake == null)
}
```

We're going to rely on `generateNextStates` to not generate a few classes of invalid states: you can't move into a wall or another snake. `isValid` then only needs to check if we're on a spike (most likely we fell onto one, it won't move onto one). But as an edge case, we need to make sure that a snake doesn't run off the edge of the map and fall forever. I did design the state so that snakes can go slightly off the edge and come back in (it's necessary for some levels), but once you start falling off the world, you're going to fall forever. 

Since `generateNextStates` will `null` snakes that reach the exit, `isSolved` only needs to check that they're all `null`. Otherwise keep going.

Okay, enough of that. Let's do the hard part: `generateNextStates`:

```javascript

let generateNextStates = function* (state) {
    // handle hitting the exits (including by falling)
    // can only exit if there are no fruits left
    if (state.fruits.size == 0) {
        for (let i = 0; i < state.snakes.size; i++) {
            let snake = state.snakes.get(i)
            if (snake === null) continue

            // if we hit an exit, remove this snake
            // only remove one snake per iteration
            if (snake.some(pt => pt.equals(state.exit))) {
                yield {
                    state: state.set('snakes', state.get('snakes').set(i, null)),
                    step: `${i}*`,
                }
                return
            }
        }
    }

    // handle gravity
    gravityEachSnake:
    for (let i = 0; i < state.snakes.size; i++) {
        let snake = state.snakes.get(i)
        if (snake == null) continue

        for (let pt of snake) {
            let ptd = pt.set('r', pt.get('r') + 1)

            // supported by a wall
            if (state.walls.has(ptd))
                continue gravityEachSnake

            // supported by another snake
            if (state.snakes.some(otherSnake => snake != null && otherSnake != null && snake != otherSnake && otherSnake.includes(ptd)))
                continue gravityEachSnake
        }

        // if we made it this far, the snake should fall one point
        let newSnake = snake.map(pt => pt.set('r', pt.get('r') + 1))

        yield {
            state: state.set('snakes', state.get('snakes').set(i, newSnake)),
            step: `${i}f`,
        }

        // Only generate a single fall per iteration
        return
    }

    // otherwise try to move each snake in each direction
    for (let i = 0; i < state.snakes.size; i++) {
        let snake = state.snakes.get(i)
        if (snake == null) continue

        for (let [d, cd, rd] of [['→', 1, 0], ['←', -1, 0], ['↓', 0, 1], ['↑', 0, -1]]) {
            // check that the square is empty
            // hitting a fruit or an exit is fine
            let pt = snake.get(0)
            pt = pt.set('r', pt.get('r') + rd).set('c', pt.get('c') + cd)

            if (state.walls.has(pt)) continue
            if (state.snakes.some(snake => snake != null && snake.includes(pt))) continue

            // move the snake by adding the new point to the front of the snake
            // if we hit a fruit, keep the last element to make the snake longer
            // otherwise, remove the end of the list to simulate movement
            let newSnake = snake.unshift(pt)
            let ateFruit = state.fruits.has(pt)
            if (!ateFruit) {
                newSnake = newSnake.pop()
            }

            let newState = state.set('snakes', state.snakes.set(i, newSnake))
            if (ateFruit) {
                newState = newState.set('fruits', newState.get('fruits').remove(pt))
            }

            yield {
                state: newState,
                step: `${i}${d}${ateFruit ? 'g' : ''}`,
            }
        }
    }
}
```

There are three cases to deal with:

* Exiting the level
* Falling
* Moving (with a substate of eating a fruit)

First, exiting. To do that, we have to make sure that all of the fruits are gone first. Then we just check if any snake ran into the exit. If so, null it out. We only ever check if one snake exited at a time and don't processing falling or moving if they do (with the early `return`). So in this case, we can only yield a maximum of one `move`. 

Next, falling. This one is a bit tricky, since we have to deal with a few different rules:

* If any segment of the snake is resting on a wall or another snake, it doesn't fall
* If the snake is resting on itself, it can fall (as long as the first point is met)

Ergo this fun condition:

```javascript
if (state.snakes.some(otherSnake => snake != null && otherSnake != null && snake != otherSnake && otherSnake.includes(ptd)))
    continue gravityEachSnake
```

If `some` `otherSnake` that is not `null` (already exited), not the same as the current `snake`, and includes any point of a wall, don't fall. Otherwise, generate an updated snake where the each row is one greater. 

The final condition is moving. Take each snake and each direction and potentially generate a move:

* If the square is occupied (by a wall, snake, or spike), don't generate that move. Otherwise, check for a fruit. If there isn't one, remove the last element of the snake and add a new head (to simulate moving). If there is, just generate a head and don't remove the tail to grow.

And that's it, we have all of the possible moves. 

```javascript
let solveSnakebird = makeSolver({ returnFirst: false, searchMode: 'bfs', debug: DEBUG, generateNextStates, isValid, isSolved })
```

Some additional wrapping code to run it on the command line here ([snakebird.js](https://github.com/jpverkamp/solvers/blob/main/snakebird.js)) and we can run it:



```text
$ node snakebird.js snakebird/0.txt

===== snakebird/0.txt =====
----------------------
--------##-----*------
--------####----------
----#----##-----------
------#--#---+-#------
---CBA---#-#---##---+-
-#######---##-------##
######################

time taken: 0.414
iterations: 11117
raw steps: start 0→ 0→ 0→ 0↓ 0→ 0→ 0↑ 0↑ 0→ 0→ 0→g 0→ 0↓ 0f 0→ 0→ 0→ 0→ 0→ 0↑ 0→g 0↑ 0← 0← 0← 0← 0↑ 0← 0↑ 0↑ 0*
combined steps: select(0; A-Z) 3→ ↓ 2→ 2↑ 4→ ↓ 5→ ↑ → ↑ 4← ↑ ← 2↑
```

That's a surprising lot of nodes to check, but it works pretty well. And because I have `returnFirst: false`, it will always find the optimal solution!

But... wait. How did I do that? Updates to `immutable.js`. When we have a solution, record rather than return. When we find a duplicate, update for shorter moves:

```javascript
// If we have a solution:
// - If we're returning the first solution, return it and steps to get to it
// - If not, record it
if (isSolved(currentState)) {
    if (returnFirst) {
        return {
            state: currentState.toJS(),
            steps: stepsTo(currentNode),
            iterations,
            duration: (Date.now() - startTime) / 1000,
            error
        }
    } else {
        solutions = solutions.add(currentState)
    }
}

// Otherwise, check:
// - If we've reached a new known state
// - If it's a known state that contains fewer steps
// Either way, do not continue processing
if (visited.has(currentState)) {
    let visitedPreviousNode = visited.get(currentState)
    if (stepsTo(currentNode).length < stepsTo(visitedPreviousNode).length) {
        visited = visited.set(currentState, currentNode)
    } else {
        currentNode = currentNode.set('previousNode', visitedPreviousNode)
    }
    continue
} else {
    visited = visited.set(currentState, currentNode)
}
```

At the end, we have to check for the shortest of the `solutions`:

```javascript
// If we've made it this far, check if we have any solutions
// We need to return the shortest one
let shortestSolvedNode = null

if (debug) console.log('SOLUTIONS')
if (debug) console.log(solutions.toJSON())

for (let state of solutions) {
    let node = visited.get(state)
    if (shortestSolvedNode === null || stepsTo(node).length < stepsTo(shortestSolvedNode).length) {
        shortestSolvedNode = node
    }
}

let result = {
    iterations,
    duration: (Date.now() - startTime) / 1000,
    error,
}

if (shortestSolvedNode) {
    result.state = shortestSolvedNode.state.toJS()
    result.steps = stepsTo(shortestSolvedNode)
}

return result
```

And that's it. We have a way to find the shortest solution to any snakebird problem!

Now... it doesn't actually work perfectly. Particularly in the case of multiple snakes, there is an explosion of states that runs out of RAM before we can solve the problem. One solution: throw more RAM at it! But I think we could use a bit more optimization first. Either an ability to persist nodes we haven't used in a while to disk or a scoring node to order our search better. 

That can wait for another day though. Onward!

Output for the first 11 levels (I need optimization for 9):

```text
$ for f in snakebird/*.txt
      node snakebird.js --progress 1000000 --timeout 60 $f
  end | tee log.txt

===== snakebird/0.txt =====
----------------------
--------##-----*------
--------####----------
----#----##-----------
------#--#---+-#------
---CBA---#-#---##---+-
-#######---##-------##
######################

time taken: 0.425
iterations: 11117
raw steps: start 0→ 0→ 0→ 0↓ 0→ 0→ 0↑ 0↑ 0→ 0→ 0→g 0→ 0↓ 0f 0→ 0→ 0→ 0→ 0→ 0↑ 0→g 0↑ 0← 0← 0← 0← 0↑ 0← 0↑ 0↑ 0*
combined steps: select(0; A-Z) 3→ ↓ 2→ 2↑ 4→ ↓ 5→ ↑ → ↑ 4← ↑ ← 2↑

===== snakebird/1.txt =====
---*--
------
#-----
+--#+#
------
-#BA--
-####-
-####-
-###--

time taken: 0.1
iterations: 1569
raw steps: start 0↑ 0← 0f 0↑ 0← 0← 0↑g 0→ 0f 0→ 0→ 0→ 0f 0↑ 0↑g 0↑ 0← 0↑ 0↑ 0*
combined steps: select(0; A-Z) ↑ ← ↑ 2← ↑ 4→ 3↑ ← 2↑

===== snakebird/2.txt =====
---##-------
---###------
--####--*---
-#####------
-##-+#---C--
-##-----AB-+
###--#####--
#######-##--
#######--#--

time taken: 0.145
iterations: 1849
raw steps: start 0← 0← 0← 0← 0← 0↑ 0f 0→ 0↑g 0← 0f 0↑ 0→ 0f 0→ 0→ 0→ 0→ 0→ 0→ 0→g 0↑ 0← 0← 0f 0← 0↑ 0↑ 0↑ 0*
combined steps: select(0; A-Z) 5← ↑ → ↑ ← ↑ 8→ ↑ 3← 3↑

===== snakebird/3.txt =====
---##-------
---###------
--####--*---
-#####------
-##-+#---C--
-##-----AB-+
###--#####--
#######-##--
#######--#--

time taken: 0.136
iterations: 1849
raw steps: start 0← 0← 0← 0← 0← 0↑ 0f 0→ 0↑g 0← 0f 0↑ 0→ 0f 0→ 0→ 0→ 0→ 0→ 0→ 0→g 0↑ 0← 0← 0f 0← 0↑ 0↑ 0↑ 0*
combined steps: select(0; A-Z) 5← ↑ → ↑ ← ↑ 8→ ↑ 3← 3↑

===== snakebird/4.txt =====
--CBA-*
--D#---
-------
#^---^#
-^-----
-^^#^--
---+---
-----#-
----##-
----##-

time taken: 0.325
iterations: 4836
raw steps: start 0↑ 0← 0← 0f 0↓ 0↓ 0→ 0f 0f 0→ 0→ 0↓ 0↓ 0← 0↓ 0← 0← 0↑ 0→g 0→ 0f 0↑ 0→ 0↑ 0↑ 0← 0← 0↑ 0→ 0↑ 0→ 0→ 0↑ 0↑ 0*
combined steps: select(0; A-Z) ↑ 2← 2↓ 3→ 2↓ ← ↓ 2← ↑ 2→ ↑ → 2↑ 2← ↑ → ↑ 2→ 2↑

===== snakebird/5.txt =====
---*-
-#---
+--+#
-----
^#--#
-BA^^
-C#^-

time taken: 0.244
iterations: 3087
raw steps: start 0↑ 0↑ 0← 0↑ 0→ 0↑ 0f 0→g 0↑ 0f 0f 0→ 0→ 0↑ 0↑ 0← 0← 0← 0↓ 0← 0f 0← 0↑g 0↑ 0↑ 0→ 0→ 0→ 0*
combined steps: select(0; A-Z) 2↑ ← ↑ → ↑ → ↑ 2→ 2↑ 3← ↓ 2← 3↑ 3→

===== snakebird/6.txt =====
---##----
---##----
--##-----
-###-----
--#+-#---
--#-----*
BA---#---
C##^-----
D-###----

time taken: 0.194
iterations: 3553
raw steps: start 0→ 0→ 0→ 0↑ 0→ 0→ 0↑ 0↑ 0← 0← 0↑ 0→ 0→ 0f 0↓ 0↓ 0← 0← 0↑ 0↑ 0↑ 0f 0f 0←g 0↓ 0f 0← 0← 0← 0← 0↑ 0→ 0→ 0f 0→ 0→ 0→ 0↑ 0→ 0→ 0→ 0→ 0*
combined steps: select(0; A-Z) 3→ ↑ 2→ 2↑ 2← ↑ 2→ 2↓ 2← 3↑ ← ↓ 4← ↑ 5→ ↑ 4→

===== snakebird/7.txt =====
------*---
----------
---#------
----------
#---------
#---------
#--#---abc
---#--ABCd
------####

time taken: 22.459
iterations: 526433
raw steps: start 0↑ 0↑ 0→ 0↑ 0← 0← 0f 1↓ 1← 1↑ 0← 0← 1↑ 1↑ 1← 1← 1← 1← 1← 1↑ 1← 0↑ 0↑ 0← 0↑ 0← 0← 1← 1↑ 1↑ 1→ 0f 1f 1→ 1→ 1↑ 1→ 0↑ 0↑ 0→ 0↑ 0→ 0→ 0→ 0→ 0→ 0* 1→ 1→ 1→ 1↑ 1*
combined steps: select(0; A-Z) 2↑ → ↑ 2← select(1; a-z) ↓ ← ↑ select(0; A-Z) 2← select(1; a-z) 2↑ 5← ↑ ← select(0; A-Z) 2↑ ← ↑ 2← select(1; a-z) ← 2↑ 3→ ↑ → select(0; A-Z) 2↑ → ↑ 5→ select(1; a-z) 3→ ↑

===== snakebird/8.txt =====
--------------*-
----------------
--CBA--------###
-EDabc-----^^^##
######^^^--^----
-#####--^^#^----

time taken: 34.044
iterations: 680995
raw steps: start 0↑ 0← 0↑ 0→ 0→ 0f 0↓ 0→ 1↑ 1→ 0→ 1↓ 1→ 0→ 0→ 1→ 0↓ 0→ 0f 1↑ 1→ 1→ 0↑ 1→ 0↑ 1↑ 1→ 1→ 1→ 1→ 0↑ 0↑ 0→ 0→ 0→ 0→ 0* 1→ 1↑ 1*
combined steps: select(0; A-Z) ↑ ← ↑ 2→ ↓ → select(1; a-z) ↑ → select(0; A-Z) → select(1; a-z) ↓ → select(0; A-Z) 2→ select(1; a-z) → select(0; A-Z) ↓ → select(1; a-z) ↑ 2→ select(0; A-Z) ↑ select(1; a-z) → select(0; A-Z) ↑ select(1; a-z) ↑ 4→ select(0; A-Z) 2↑ 4→ select(1; a-z) → ↑

===== snakebird/9.txt =====
----*---
--------
--------
----#^--
--------
--------
---^^---
-#------
-----#--
--------
--------
CBA--ab-
D#####cd
####-##e

time taken: 60.003
iterations: 628280
error: maxTime reached

===== snakebird/10.txt =====
-###-----
####-*---
---#-----
-+-#---D#
-----ABC#
--####-##
---###-#-
-----#-+-
-----#-##
-----#-##
----##-##
----####-

time taken: 0.579
iterations: 16740
raw steps: start 0↑ 0→ 0↑ 0↑ 0f 0↑ 0f 0f 0f 0f 0f 0f 0→g 0→ 0→ 0→ 0↑ 0← 0← 0f 0← 0← 0↑ 0↑ 0↑ 0← 0← 0← 0← 0← 0← 0↑ 0→g 0↑ 0→ 0f 0f 0→ 0→ 0→ 0↑ 0↑ 0↑ 0*
combined steps: select(0; A-Z) ↑ → 3↑ 4→ ↑ 4← 3↑ 6← ↑ → ↑ 4→ 3↑
```

Pretty cool. Next up, optimization! 

Source: 

* [snakebird.js](https://github.com/jpverkamp/solvers/blob/main/snakebird.js)
* [solvers/immutable.js](https://github.com/jpverkamp/solvers/blob/main/solvers/immutable.js)
