---
title: "AoC 2021 Day 4: His Name Oh"
date: 2021-12-04 00:00:10
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Giant Squid](https://adventofcode.com/2021/day/4)

#### **Part 1:** Given a set of bingo boards and a list of numbers, find the first board to win. Multiply the sum of the un-called numbers on that board times the last number called. 

<!--more-->

This one was kind of neat! First time that I'm going to break out a few helper functions. First, something to read in the data in the specified format:

* The first line contains a comma-delimited list of numbers in the order they will be called followed by an empty line
* Subsequent lines consist of a 5x5 grid of space delimited numbers (bingo cards) followed by a new line

Let's read it in:

```python
BingoBoard = List[List[Optional[str]]]

def parse(file: typer.FileText) -> Tuple[List[Int], BingoBoard]:
    '''Parse a bingo definition. Return the list of numbers (as ints) and a list of 5x5 grids.'''

    numbers = [int(el) for el in file.readline().split(',')]
    file.readline()

    boards = []
    board = []

    for line in file:
        if not line.strip():
            continue

        board.append([int(el) for el in line.split()])

        if len(board) == 5:
            boards.append(board)
            board = []

    return numbers, boards
```

This time, we're using the `typer.FileText` as an actual file object where we can read off the first line (for numbers), the empty line, and then starting the iteration to read five lines at a time (skipping empty lines). Straight forward enough.

Next, we're going to write a helper that can take a Bingo board and a number and cross off that number (by marking it as `None`):

```python
def check_off(board: BingoBoard, number: int):
    '''Remove the given number from the given board by changing it to None.'''

    # Yes, I know I'm hardcoding 5
    for i in range(5):
        for j in range(5):
            if board[i][j] == number:
                board[i][j] = None
```

No problems, because `BingoBoard` is defined to to be `Optional[int]`, either `int` or `None`.

Next up, check if a Bingo board is solved. I'm particularly proud of this monster:

```python
def is_solved(board):
    '''Return True if any row or column is completely None.'''

    # This is silly looking
    return (
        any(
            all(board[i][j] is None for j in range(5))
            for i in range(5)
        ) or
        any(
            all(board[i][j] is None for i in range(5))
            for j in range(5)
        )
    )
```

As I said. It's silly looking. Essentially, is `any` row made of `all` `None` in each column or is any `column` made of all `None` for each row. I'm curious what 'cleaner' ways there would be to write that. 

Anyways, once you have all that, the actual 'solution' is really short:

```python
def part1(file: typer.FileText):

    numbers, boards = parse(file)

    for number in numbers:
        for board in boards:
            check_off(board, number)

            # As soon as any board is solved, we're done
            if is_solved(board):
                remaining_numbers = [el for row in board for el in row if el]
                print(f'{remaining_numbers=}, {sum(remaining_numbers)=}, {number=}, product={sum(remaining_numbers)*number}')
                return
```

#### **Part 2:** Repeat Part 1, but instead of the first board solved, use the numbers remaining on the last board after it's solved.

Again, we have the pieces, it's a matter of turning that into code:

```python
def part2(file: typer.FileText):

    numbers, boards = parse(file)

    for number in numbers:
        for board in boards:
            check_off(board, number)

        # If (and only if) we're on the last board, check for a solution and bail
        if len(boards) == 1 and (board := boards[0]) and is_solved(board):
            remaining_numbers = [el for row in board for el in row if el]
            print(f'{remaining_numbers=}, {sum(remaining_numbers)=}, {number=}, product={sum(remaining_numbers)*number}')
            return

        # Otherwise, remove solved boards
        boards = [board for board in boards if not is_solved(board)]
```

Breaking functionality into functions really does make for relative elegant code. 

#### Timing

Still quick, but about twice as slow as previous examples. I expect that I could cut some time out with a more efficient data structure... but it still runs in a fraction of a second. 

```bash
--- Day 4: Giant Squid ---

$ python3 his-name-oh.py part1 input.txt
remaining_numbers=[99, 19, 9, 59, 92, 82, 69, 72, 2, 45, 93, 27], sum(remaining_numbers)=668, number=66, product=44088
# time 54675500ns / 0.05s

$ python3 his-name-oh.py part2 input.txt
remaining_numbers=[3, 78, 23, 79, 80], sum(remaining_numbers)=263, number=90, product=23670
# time 66984792ns / 0.07s
```

#### Type checking

One thing that I've been doing is putting type annotations on everything and then (finally) running `mypy` against it. That's pretty cool:

```bash
$ mypy his-name-oh.py
Success: no issues found in 1 source file
```

(I had a few to fix.)