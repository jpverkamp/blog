---
title: Solving Loop Puzzles
date: 2016-07-14
programming/languages:
- Python
---
A quick puzzle from Daily Programmer:


> ∞ Loop is a mobile game that consists of n*m tiles, placed in a n*m grid. There are 16 different tiles:

> `┃, ━, ┏, ┓, ┛, ┗, ┣, ┳, ┫, ┻, ╋, ╹, ╺, ╻, ╸, ' '.`

> The objective is to create a closed loop: every pipe must have another tile facing it in the adjacent tile `—` for example if some tile has a pipe going right, its adjacent tile to the right must have a pipe going left.


The most straightforward solution is a hybrid combination of constraints and backtracking, similar to what I did when solving [Takuzu]({{< ref "2015-10-29-takuzu-solvers.md" >}}) and [tile puzzles]({{< ref "2014-10-28-tile-puzzle.md" >}}).

<!--more-->

First, we'll create two classes, one for individual characters and one for puzzles. Think what you may about {{< wikipedia "object oriented programming" >}}, but I think it fits fairly well with this problem.

First, characters. We want something that will be able to represent characters with with their character form (the {{< wikipedia "box drawing characters" >}} above) or as a collection of edges (if the top / right / bottom / left pipe is included). This could be represented as a 4-bit integer, but instead I'll use a 4-tuple of bools. It's just a bit easier to read by default.

On top of that, we want functions that can rotate pieces, test if two characters are actually the same, and to test if two neighboring pieces can border each other or not. The last is true if they either both have a pipe pointing inwards or neither does.

```python
class Character(object):
    '''A box drawing character or empty space ( ╸╻┓╺━┏┳╹┛┃┫┗┻┣╋).'''

    order = ' ╸╻┓╺━┏┳╹┛┃┫┗┻┣╋'
    sides = {'top': (0, 2), 'right': (1, 3), 'bottom': (2, 0), 'left': (3, 1)}

    def __init__(self, symbol_or_bits):
        '''
        Create a new character from either the symbol (must be a valid symbol)
        or a 4-tuple of booleans representing the sides (top, right, bottom,
        left).
        '''

        if isinstance(symbol_or_bits, str):
            self.symbol = symbol_or_bits

            bits = bin(Character.order.find(symbol_or_bits))[2:]
            bits = '0' * (4 - len(bits)) + bits

            self.bits = tuple(bit == '1' for bit in bits)
        else:
            self.bits = symbol_or_bits
            self.symbol = Character.order[int(''.join('1' if bit else '0' for bit in symbol_or_bits), 2)]

    def rotate(self):
        '''Return the next rotation for this character.'''

        return Character(tuple(self.bits[i] for i in range(-1, 3)))

    def rotations(self):
        '''Generate all four of the rotations this character could have.'''

        c = self
        for i in range(4):
            yield c
            c = c.rotate()

    def can_neighbor(self, other, side):
        '''
        Test if this character can neighbor a given other on a given side.

        Two characters can be neighbors if they either both have a line on that
        side or neither does. If other is not set, that is assumed to be a
        outside of the puzzle and thus not have a line.
        '''

        my_bit, their_bit = Character.sides[side]

        # print(side, self, other, my_bit, their_bit, self.bits, other.bits) # DEBUG

        if other:
            return self.bits[my_bit] == other.bits[their_bit]
        else:
            return not self.bits[my_bit]

    def __hash__(self):
        '''Use the symbol as a hash. This is so we can put characters in sets.'''

        return hash(self.symbol)

    def __eq__(self, other):
        '''Characters are equal if they have the same symbol.'''

        return self.symbol == other.symbol

    def __repr__(self):
        '''Print which character this is.'''

        return self.symbol
```

After that, the next step will be to create a `Puzzle`. This is the grid of characters, but we'll actually go a step larger. Each cell in the `Puzzle` will actually be a set of rotations that are still possible. This means that as long as any cell has more than 1 possibility, it's not solved. If any has managed to reach 0, no solution is possible.

In addition, we'll put the constraining function here. This will loop through every single cell in the puzzle: for each, it will match each rotation remaining against each rotation of all four neighbors. If a given rotation cannot possibly match any one of the neighbors, remove it from the set. Imagine:

```test
┛╸╸
╺┓╻
┗ ┣
```

The middle character can originally be any of `{┏, ┓, ┛, ┗}`; however, the bottom center is an empty space, so we should not include any downward facing options. Thus, with a single round of constraint, we've reduced the center tile to `{┛, ┗}`. Even better, this will further constrain the top center piece. At first it was `{╹, ╺, ╻, ╸}`, but the center has to have an upward pointing point, forcing the top center to be `{╻}`. Each round of constraints only sets each tile once and won't work recursively, but it's easy enough to call it more than once. Especially since the function will return `True` until the puzzle reaches a steady state.

```python
class Puzzle(object):
    '''Represent a grid of possible characters.'''

    border = {Character(' ')}

    def __init__(self, data):
        '''Initialize from a string containing characters.'''

        self.data = [
            [set(Character(c).rotations()) for c in line]
            for line in data.strip().split('\n')
        ]
        self.rows = len(self.data)
        self.cols = len(self.data[0])

    def possibilities(self):
        '''
        Return the number of possibilities in the form (unsolved squares, total
        possibilities). A solved puzzle will return (0, rows * cols).
        '''

        return (
            sum(0 if len(el) == 1 else 1 for row in self.data for el in row),
            sum(len(el) for row in self.data for el in row)
        )

    def is_solvable(self):
        '''Test if the puzzle is still solvable (no empty possibilities.)'''

        return not any(
            len(el) == 0
            for row in self.data
            for el in row
        )

    def is_solved(self):
        '''Test if this puzzle is currently solved.'''

        return all(
            len(el) == 1
            for row in self.data
            for el in row
        )

    def constrain(self):
        '''
        Constrain this puzzle by removing any rotations that could not possibly
        be used (there's no possibility in the neighbor to match them).

        Only make one pass, call this function multiple times in case one
        constraint cascades.

        Return if anything changed.
        '''

        logging.debug('Applying constraints, possiblities: {}'.format(self.possibilities()))

        offsets = [
            ('top', -1, 0),
            ('right', 0, 1),
            ('bottom', 1, 0),
            ('left', 0, -1),
        ]

        something_changed = False

        for row in range(self.rows):
            for col in range(self.cols):
                invalid = set()
                for first_point in self[row, col]:
                    if not all(
                        any(
                            first_point.can_neighbor(second_point, direction)
                            for second_point in self[row + row_offset, col + col_offset]
                        ) for direction, row_offset, col_offset in offsets
                    ):
                        invalid.add(first_point)

                for impossibility in invalid:
                    something_changed = True
                    self[row, col].remove(impossibility)

        return something_changed


    def __getitem__(self, pt):
        '''
        Fetch the current possibility set from a given row and column.

        If the index is out of bounds, instead return a 'border character' with
        no edges to help guarantee that no pieces point outwards.
        '''


        row, col = pt
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.data[row][col]
        else:
            return Puzzle.border

    def __repr__(self):
        '''If solved, print the puzzle; if not, print remaining possibilities.'''

        if self.is_solved():
            return '\n'.join(
                ''.join(str(list(el)[0]) for el in row)
                for row in self.data
            )

        else:
            def pad_set(el):
                return ''.join(str(each) for each in el) + ' ' * (4 - len(el))

            line_seperator = '\n' + ('┈' * (7 * self.cols - 3)) + '\n'

            return line_seperator.join(
                ' ┆ '.join(pad_set(el) for el in row)
                for row in self.data
            )
            return repr(self.data)
```

That's actually enough by itself to solve some puzzles. But sometimes, particularly in larger puzzles, you'll reach states where two arrangements are still possible. In those cases, we want to take a {{< wikipedia "backtracking" >}} step: choose each of the possible states in turn and assume it is correct, switching back to the constraint solver until the next block. If a solution is found in that branch, just return. If not, try the next branch from that position.

```python
def solve(puzzle):
    '''
    Use a hybrid constraint / backtracking solver to solve the puzzle.

    while not solved:
        apply constraint solver until it doesn't work any more
        find the first mismatched point and try each possibility
    '''

    queue = [puzzle]
    while queue:
        puzzle = queue.pop()
        logging.info('Running backtracker, states: {}, possiblities in current state: {}'.format(len(queue), puzzle.possibilities()))
        logging.debug(puzzle)

        # Apply constraint until the constrain function returns false
        while puzzle.constrain(): pass
        logging.debug(puzzle)

        if not puzzle.is_solvable():
            logging.info('Unsolveable state found, removing it')
            continue

        if puzzle.is_solved():
            logging.info('Solved state found, returning it')
            return puzzle

        # Split to backtracking
        def first_unclear_point():
            for row in range(puzzle.rows):
                for col in range(puzzle.cols):
                    if len(puzzle[row, col]) > 1:
                        return row, col, puzzle[row, col]

        row, col, possibilities = first_unclear_point()
        for possibility in possibilities:
            copied_puzzle = copy.deepcopy(puzzle)
            copied_puzzle[row, col].clear()
            copied_puzzle[row, col].add(possibility)

            queue.append(copied_puzzle)

    # If we made it out of the loop, there is no solution to the puzzle
    return None
```

And that's it. We can solve puzzles from `stdin`:

```python
import sys
puzzle = Puzzle(sys.stdin.read())
solution = solve(puzzle)
print(solution)
```

Example running:

```bash
$ cat 10x10.loops

┗┣┃┃┗┏┳┓┛┏
┗┛┛━┳┫┃┃━━
┛┛━┓┳╋┫━┣┏
┫╋┻┛┛┻━┳╋┗
┛┳┃┳┃╋┫┃┳┗
┓━┓━┏╋┏┻╋┓
┛┛━┃┻┗┓┓┳┓
┏╋╋┏┏┳┣┗┗┗
┣╋╋┏┏┻┓┓┏┫
┏┏┗┫┣┳┳━┫┗

$ cat 10x10.loops | python3 loop-solver.py

┏┳━━┓┏┳┓┏┓
┗┛┏━┻┫┃┃┃┃
┏┓┃┏┳╋┫┃┣┛
┣╋┻┛┗┫┃┣╋┓
┗┻━┳━╋┫┃┣┛
┏━┓┃┏╋┛┣╋┓
┗┓┃┃┣┛┏┛┣┛
┏╋╋┛┗┳┻┓┗┓
┣╋╋┓┏┫┏┛┏┫
┗┛┗┻┻┻┻━┻┛
```

Cool. Looking at this and several other puzzles, it seems like it would be a good generic framework to work out. Given a definition for a puzzle with an `is_valid` function (`can_neighbor` here), a `constrain` function, and the backtracking code above, it should be able to solve a large class of puzzles. {{< wikipedia "Sudoku" >}}, for example, or {{< wikipedia "Hashi" >}}. Both puzzles I've been working on solvers for. Even better, once you have a solver you can use it to generate puzzles with a difficulty gradient. Just solve each puzzle, keeping track of how many times you had to backtrack and how many were solved with the constraints.

And that's it. A fun little puzzle.
