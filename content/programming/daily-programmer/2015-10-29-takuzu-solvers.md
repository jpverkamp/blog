---
title: Takuzu solver
date: 2015-10-29
programming/languages:
- Python
programming/sources:
- Daily Programmer
programming/topics:
- Backtracking
- Graphs
- Heuristics
---
Based on a <a href="">/r/dailyprogrammer</a> puzzle: <a href="https://www.reddit.com/r/dailyprogrammer/comments/3pwf17/20151023_challenge_237_hard_takuzu_solver/">Takuzu solver</a>.

Basically, Takuzu is a logic puzzle similar to Sudoku. You are given a grid partially filled with 0s and 1s. You have to fill in the rest of the grid according to three simple rules:


* You cannot have more than three of the same number in a line
* Each column must have an equal number of 0s and 1s[^1]
* No two rows or no two columns can be identical


Thus, if you have a puzzle like this:

```text
0.01.1
0....1
..00..
..00..
1....0
10.0.0
```

One valid solution (most puzzles should have only a single valid answer, but that doesn't always seem to be the case):

```text
010101
001101
110010
010011
101100
101010
```

Let's do it!

<!--more-->

First, we need some sort of structure to represent and read in a Takuzu board. I think I'm going to over-engineer a little bit here, since I think it will be helpful in the long run.

My basic idea is to represent it in a way without mutation, that is to say once I've created a board, that board will never change. That will make it easier to write a backtracking solution, since when we need to back up to a previous state, we just throw away any of the derivative boards.

Taking that a level further, let's represent the Takuzu board as a base board with an essentially a 'changelog' on top of it, storing any differences from the boards 'under' it. Something like this:

```text
....    ..1.    ....    ..1.
0.0. {- .... {- .... == 0.0.
..0.    ....    ....    ..0.
...1    ..1.    .0..    .011
```

In that diagram, the board on the far left is the first layer, then the second is the next layer up, and the third is the final layer. The fourth image is the virtual board that any user of the program would actually see.

So how do we turn that into code?

```python
class Takuzu(object):

    def __init__(self, filename = None, parent = None):
        '''
        Represent a Takuzu puzzle (a grid of 0, 1, and .)

        If filename is set, load from file.
        If parent is set, extend that Takuzu puzzle.

        If neither or both is set, that is an error.
        '''

        if not (filename or parent) or (filename and parent):
            raise Exception('Set exactly one of filename and parent')

        self.size = 0
        self.tiles = collections.defaultdict(lambda : False)
        self.parent = False

        if parent:
            self.size = parent.size
            self.parent = parent

        elif filename:
            with open(filename, 'r') as fin:
                for row, line in enumerate(fin):
                    for col, char in enumerate(line.strip()):
                        if char in '01':
                            self.tiles[row, col] = char

                        self.size = col + 1

    def get(self, row = None, col = None):
        '''
        Access a tile in the current puzzle, return False for unset values

        If the current puzzle doesn't have a value set, recur to parents.
        If either row or col is set to None, return that entire row or column.
        If neither is set, return nested lists containing all current values.
        '''

        # Note: We need the ugly != None to correctly deal with row or col = 0.
        # Sometimes truthiness is annoying.

        if row != None and col != None:
            return self.tiles[row, col] or (self.parent and self.parent.get(row, col))
        elif row != None:
            return [self.get(row, col) for col in range(self.size)]
        elif col != None:
            return [self.get(row, col) for row in range(self.size)]
        else:
            return [
                [self.get(row, col) for col in range(self.size)]
                for row in range(self.size)
            ]

    def set(self, row, col, val):
        '''
        Create a child Takuzu object with the specific value set.

        If either row or column is set to None, fill any empty elements in that entire row
        with the given value.
        '''

        child = Takuzu(parent = self)

        if row != None and col != None:
            child.tiles[row, col] = val
        elif row != None:
            for col in range(self.size):
                if not child.get(row, col):
                    child.tiles[row, col] = val
        elif col != None:
            for row in range(self.size):
                if not child.get(row, col):
                    child.tiles[row, col] = val
        else:
            raise Exception('Must set at least one of row and column')

        return child
```

The interesting bits here are the `get` and `set` methods. `get`, as mentioned, assumes the layered structure above. It will start on the topmost layer (the actual object the program has a reference to) and try to look up the given point. If that fails (we're using a `collections.defaultdict`, so every reference will either by `'0'`, `'1'`, or `False`), fall back to the next layer up (the `parent`) until we either find one or run out of `parent` nodes.

Similarly, `set` doesn't actually change the current Takuzu object. Instead, it creates a new object with the current one as its parent, setting the new value in the child. This means that any values that were previously set are transparently available in the child, but we can at any point backtrack so long as we keep a reference to the now parent object around.

In addition, I've gone ahead and built in a bit of functionality that I know we're going to need into `get` and `set`. In either case, if you only specify either the `row` or `col` and leave the other empty (`None`), then we will return that entire row or column (or `set` any empty values). That's easy enough to code and it has the advantage of making it easy to compare rows to one another (for the third requirement above).

Okay, up next, we'll probably want a few more helper functions in this class in order to actually tell when we've solved one of these puzzles so the algorithms we eventually write can actually terminate:

```python
class Takuzu(object):
    ...

    def __eq__(self, other):
        '''Check if two Takuzu puzzles are equal.'''

        for row in range(self.size):
            for col in range(self.size):
                if self.get(row, col) != other.get(row, col):
                    return False

        return True

    def __str__(self):
        '''Return a string representation the same as can be read from a file.'''

        out = ''

        for row in range(self.size):
            for col in range(self.size):
                out += str(self.get(row, col) or '.')
            out += '\n'

        return out

    def is_full(self):
        '''If all values have been filled in.'''

        for row in range(self.size):
            for col in range(self.size):
                if not self.get(row, col):
                    return False

        return True

    def is_valid(self):
        '''Test if the current is still possibly a valid solution. If it also is_full,
        the board is solved.'''

        # Cannot have three identical numbers in a line
        # Ignore unset pieces
        for row in range(self.size):
            for col in range(self.size):
                if not self.get(row, col):
                    continue

                if self.get(row - 1, col) == self.get(row, col) == self.get(row + 1, col):
                    return False

                if self.get(row, col - 1) == self.get(row, col) == self.get(row, col + 1):
                    return False

        # All rows and columns must have no more than the maximum (size/2) number of 0s or 1s
        for index in range(self.size):
            if (
                self.get(index, None).count('0') > self.size / 2
                or self.get(index, None).count('1') > self.size / 2
                or self.get(None, index).count('0') > self.size / 2
                or self.get(None, index).count('1') > self.size / 2
            ):
                return False

        # No two rows or columns can be equal (ignore rows/columns that contain unset values)
        # all(...) on a row or column will be true iff all values are set
        for first_index in range(self.size):
            for second_index in range(first_index):
                if (
                    all(self.get(first_index, None))
                    and all(self.get(None, first_index))
                    and (
                        self.get(first_index, None) == self.get(second_index, None)
                        or self.get(None, first_index) == self.get(None, second_index)
                    )
                ):
                    return False

        # Whee passed all three conditions!
        return True

    def is_solved(self):
        '''Return True iff this puzzle is solved.'''

        return self.is_full() and self.is_valid()
```

`__eq__` and `__str__` are 'magic' methods in Python that will define equality and converting this object to a string respectively. This will be nice to make sure we don't investigate the same board more than once later.

After that, we have `is_full`, `is_valid`, and `is_solved`[^2]. In the first case, we're checking if a puzzle has everything filled in. That way we know if we can stop recurring one way or the other.

`is_valid` is actually a relatively new method. Before that, I could only check if a puzzle `is_solved`, but this way we can eliminate entire branches of the search space much earlier. For example, as soon as a backtracking solution places the third `0` in a row, it can stop looking down that path since `is_valid` will return `False`. Finally, `is_solved`. It used to have most of the `is_valid` code, but once that method existed, a puzzle `is_solved` simply if both it `is_full` and it `is_valid`. Easy enough.

So how do we actually solve a puzzle with this?

Let's start with the simple (relatively speaking, since we've done it before) backtracking solution. Given everything that we have in the Takuzu class, the actual solver is actually really simple:

```python
def solve(takuzu):
    '''Solve a puzzle using backtracking (also a fall back for the human solver).'''

    queue = [takuzu]

    while queue:
        takuzu = queue.pop()

        # Solved, we're done!
        if takuzu.is_solved():
            return takuzu

        # If we don't have a valid solution, stop looking on this branch
        if not takuzu.is_valid():
            continue

        # Otherwise, find one empty spot and try both possiblities
        def enqueue():
            for row in range(takuzu.size):
                for col in range(takuzu.size):
                    if not takuzu.get(row, col):
                        for value in '01':
                            queue.insert(takuzu.set(row, col, value), 0)
                        return
        enqueue()

    return False
```

Basically, we keep a stack of solutions, which will allow us to perform a [[wiki:depth-first search]]()[^3].

Basically, create a branch, trying first a `0` in the first empty spot. Looking down that path, if we find a solution, we're done. If we don't try a `1` instead. That's really it. And it's actually relatively fast.

Given the input:

```test
0..1.0
0.11..
......
......
1..1..
.....0
```

We can solve it easily enough:

```bash
$ python3 takuzu.py --method backtracker sample_6x6.takuzu

010110
001101
110010
011001
100101
101010

Solved in 0.15 seconds
```

Nice. (You can check out the <a href="https://github.com/jpverkamp/takuzu">full source</a> if you'd like to see how I'm handling the command line parameters along with a few other goodies.[^4])

Unfortunately, as puzzles get a bit larger, that runtime isn't so great:

```bash
$ python3 takuzu.py --method backtracker sample_8x8.takuzu

10011010
11001100
01100101
10110010
01011001
01001101
10100110
00110011

Solved in 47.03 seconds
```

Yeah...

We can do better.

How about instead of trying to solve the puzzle like a computer (brute forcing it), let's apply some heuristics more like a human would solve the puzzle. For example, if we see a pair of 0s next to each other, we know the tile on either side of it is a 1 (likewise for a pair of 0s separated by a single space and said space):

```python
def __third_of_a_kind__(takuzu):
    '''If adding a value would make three in a row, add the other.'''

    for row in range(takuzu.size):
        for col in range(takuzu.size):
            if takuzu.get(row, col):
                continue

            for ((offset1_row, offset1_col), (offset2_row, offset2_col)) in [
                # Two already in a line
                (( 0,  1), ( 0,  2)),
                (( 0, -1), ( 0, -2)),
                (( 1,  0), ( 2,  0)),
                ((-1,  0), (-2,  0)),
                # Two with a hole in between
                (( 0,  1), ( 0, -1)),
                (( 1,  0), (-1,  0)),
            ]:

                val1 = takuzu.get(row + offset1_row, col + offset1_col)
                val2 = takuzu.get(row + offset2_row, col + offset2_col)

                if val1 and val2 and val1 == val2:
                    return takuzu.set(row, col, invert(val1))

    return False
```

Basically, for each empty tile in the current puzzle, compare each of six pairs. Either those in the four cardinal directions or the pair on either side horizontally or vertically.

Next rule, let's look for rows where we already have the necessary number of 0s and only need 1s. We can just fill those out:

```python
def __fill_rows__(takuzu):
    '''If we can figure out how many 0s and 1s we need for each and any row/col needs
    only 0s or 1s, add them'''

    # Try to fill any rows that have all of the needed 0s/1s but not the other
    for index in range(takuzu.size):
        for row, col in [(index, None), (None, index)]:
            for value in '01':
                # Have enough of 'value'
                if takuzu.get(row, col).count(value) == takuzu.size / 2:
                    # Not enough of the other one
                    if takuzu.get(row, col).count(invert(value)) < takuzu.size / 2:
                        return takuzu.set(row, col, invert(value))

    return False
```

It's neat how short that code is.

Finally (for the moment at least), let's write a slightly more complicated method. This time, let's take a single row or column and generate all the possible ways we can fill it out. Then remove those that would either lead to a duplicate or three in a row. If we have only exactly one row left, then we're golden. That's our row:

```python
def __fill_by_duplicates__(takuzu):
    '''Fill a puzzle by checking if any rows/cols are near enough to done that only one
    possibility is left.'''

    def row_or_col(which, index):
        if which == 'row':
            return takuzu.get(index, None)
        else:
            return takuzu.get(None, index)

    for major in ('row', 'col'):
        # Completed rows/cols have no Nones (so are 'all')
        completed = filter(all, [
            row_or_col(major, index)
            for index in range(takuzu.size)
        ])

        for index in range(takuzu.size):
            current = row_or_col(major, index)

            # Already a complete row/col, skip it
            if all(current):
                continue

            # Generate all posibilities, removing any that we already see
            possibilities = [
                option
                for option in permute_nones(current)
                if (
                    option not in completed
                    and option.count('0') == takuzu.size / 2
                    and option.count('1') == takuzu.size / 2
                    and '000' not in ''.join(option)
                    and '111' not in ''.join(option)
                )
            ]

            # If we have exactly one, set that one
            if len(possibilities) == 1:
                for other_index, value in enumerate(possibilities[0]):
                    if major == 'row':
                        takuzu = takuzu.set(index, other_index, value)
                    else:
                        takuzu = takuzu.set(other_index, index, value)

                return takuzu

    # Never found one
    return False
```

I'm not nearly as happy with this rule as I am with the other two. Mostly because of the difference between rows and columns, the code is a little strange. The core of it is the `permute_nones` helper, which will take a list containing some number of `None` entries and fill them each with either a `0` or `1`, generating all possibilities:

```python
def permute_nones(ls):
    '''Helper function to generate all permutations from filling in 0s and 1s into a list'''

    if ls == []:
        yield []
    elif ls[0]:
        for recur in permute_nones(ls[1:]):
            yield [ls[0]] + recur
    else:
        for value in '01':
            for recur in permute_nones(ls[1:]):
                yield [value] + recur
```

And that's all of my rules from now. The basic algorithm will be to apply each of those three rules in turn (since even after one has stopped working, another may 'unblock it'). If we get to the point where none of those three rules work, fall back to the backtracker we discussed above:

```python
RULES = [
    __third_of_a_kind__,
    __fill_rows__,
    __fill_by_duplicates__,
    solvers.backtracker.solve,
]

def solve(takuzu):
    '''Solve a Takuzu puzzle much as a human would: by applying a series of logical rules.'''

    while True:
        updated = False

        # If we've already solved it, return
        if takuzu.is_solved():
            return takuzu

        # Try to apply each rule in turn; if any rule works start over
        for rule in RULES:
            next_takuzu = rule(takuzu)

            if next_takuzu:
                takuzu = next_takuzu
                updated = True
                break

        # If we didn't apply any rule this iteration, done trying
        if not updated:
            break

    return takuzu
```

Since we don't have to use the much slower (runtime {{< inline-latex "O(2^n)" >}}) backtracking solution for the entire puzzle, this should run significantly faster:

```python
$ python3 takuzu.py --method human sample_6x6.takuzu

010110
001101
110010
011001
100101
101010

Solved in 0.13 seconds

$ python3 takuzu.py --method human sample_8x8.takuzu

10011010
11001100
01100101
10110010
01011001
01001101
10100110
00110011

Solved in 37.23 seconds
```

Okay. So 0.13 seconds isn't *that* much faster than 0.15 seconds, and 37.23 seconds is only a bit faster than 47.03 seconds. For easier puzzles (those where a human wouldn't have to guess), you'll get a better improvement. These were considered 'hard'.

We can do better though.

Right now, we fall back to a pure backtracking solution rather than the faster human rules if we ever fail to advance. What if we combined the two models? Use the human solution until you get stuck; then advance exactly one step with the backtracking model; then switch back to the human model. If that branch fails, you reset back to the backtracking step, the human steps can be skipped for this.

Let's try it:

```python
RULES = copy.copy(solvers.human.RULES)
RULES.remove(solvers.backtracker.solve)

def solve(takuzu):
    '''
    Solve a puzzle using a hybrid model.

    Start with the human solver.
    Every time you get stuck, guess at a spot.
    Switch back to the human solver (backtracking to step 2 on failures).
    '''

    queue = [takuzu]

    while queue:
        takuzu = queue.pop()

        # Solved, we're done!
        if takuzu.is_solved():
            return takuzu

        # If we don't have a valid solution, stop looking on this branch
        if not takuzu.is_valid():
            continue

        # Try to advance using the human rules until they all fail
        while True:
            updated = False
            for rule in RULES:
                next_takuzu = rule(takuzu)

                if next_takuzu:
                    takuzu = next_takuzu
                    updated = True
                    break

            if not updated:
                break

        # Solved, we're done!
        if takuzu.is_solved():
            return takuzu

        # Once they've failed, find one empty spot and try both possibilities
        def enqueue():
            for row in range(takuzu.size):
                for col in range(takuzu.size):
                    if not takuzu.get(row, col):
                        for value in '01':
                            queue.append(takuzu.set(row, col, value))
                        return
        enqueue()

    return False
```

So how much does that buy us?

```python
$ python3 takuzu.py --method hybrid sample_6x6.takuzu

010110
001101
110010
011001
100101
101010

Solved in 0.05 seconds

$ python3 takuzu.py --method hybrid sample_8x8.takuzu

10011010
11001100
01100101
10110010
01011001
01001101
10100110
00110011

Solved in 0.67 seconds
```

Hah! That's more like it!

For now, that's it[^5]. If you'd like to see how I structured the code (it's big enough to spread into multiple files), how I parsed command line parameters, or how I dynamically load the various solvers, you can see the entire code on GitHub: <a href="https://github.com/jpverkamp/takuzu">jpverkamp/takuzu</a>.

I like puzzles. Perhaps I'll try [[wiki:Suduko]]() next. Or maybe [[wiki:Hashi puzzles|Hashiwokakero]]()[^6]. Onwards![^7]

[^1]: For the longest time, I thought this meant you could have something like four 0s and two 1s, so long as you had that in every row and column; turns out that's not the case and a 6x6 will always have exactly three each of 0s and 1s
[^2]: I miss being able to use mostly arbitrary characters in function names
[^3]: If we wanted a [[wiki:breadth-first search]](), we would use a queue instead. Although in practice it doesn't seem to actually matter much.
[^4]: Animation!
[^5]: It turns out there are some large collections of puzzles online. One such site is <a href="http://www.binarypuzzle.com/puzzles.php">binarypuzzle.com</a>. They have puzzles ranging in size from 6x6 up to 14x14 in 4 difficulty levels, 100 of each. That's a total of 2000 puzzles. I have a script to solve all of them with each solver, but it's still running. Another day.
[^6]: I actually started on a solver for Hashi puzzles first, but my intial model didn't work out nearly as cleanly
[^7]: Alteratively, perhaps I'll try generating Takuzu puzzles instead. With a fast enough humanish solver, that should be relatively easy to do.