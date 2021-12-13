---
title: "AoC 2021 Day 10: Chunkinator"
date: 2021-12-10 00:00:15
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
---
### Source: [Syntax Scoring](https://adventofcode.com/2021/day/10)

#### **Part 1:** Given a sequence of () [] {}, and <> with nesting allowed. Find the first syntax error (where the wrong closing symbol is used). Scoring 3, 57, 1197, and 25137 respectively for each error, calculate the total error score. 

Interesting. Let's use Python exceptions! 

```python
# Using the strings directly is fine for python, but not mypy
# chunkinator.py:38: error: Unpacking a string is disallowed
pairs = [tuple(pair) for pair in ['()', '[]', '{}', '<>']]

@dataclass
class ParseMismatchException(Exception):
    expected: str
    actual: str


def parse(line: str):
    '''
    Parse a line of matching pairs. For every left, you must match the corresponding right (respecting nesting).

    If a mismatch is detected, raise a ParseMismatchException containing the expected/actual character.

    Otherwise, return True
    '''

    stack = []

    for c in line:
        matched = False

        # Start a new matching pair
        for left, right in pairs:
            if c == left:
                stack.append(right)
                matched = True
        if matched:
            continue

        # Otherwise, we have a closing character, check the stack
        if c == (top := stack.pop()):
            continue

        # Otherwise, we have a failed match
        raise ParseMismatchException(expected=top, actual=c)
    # Otherwise, yay!
    return True
```

I expect that we'll want to do something with 'incomplete' matches in Part 2, but we haven't had to do that yet. So let's use this to solve the problem!

```python
def part1(file: typer.FileText):

    scores = {')': 3, ']': 57, '}': 1197, '>': 25137}
    total_score = 0

    for line in file:
        line = line.strip()

        try:
            parse(line)

        except ParseMismatchException as ex:
            total_score += scores[ex.actual]

    print(total_score)
```

I like it when the parsing function does most of the work!

```bash
$ python3 chunkinator.py part1 input.txt
167379
```

<!--more-->

#### **Part 2:** Skip lines with errors from Part 1. Instead, find the sequence of characters that would correctly complete all open matches and convert it to a base 5 number with ), ], }, and > as 1, 2, 3, and 4 respectively (no 0). Find the mean score of all completed lines. 

The last condition is a bit weird, but we can expand our parsing function with a second exception easily enough!

```python
def parse(line: str):
    '''
    Parse a line of matching pairs. For every left, you must match the corresponding right (respecting nesting).

    If a mismatch is detected, raise a ParseMismatchException containing the expected/actual character.
    If the parse is incomplete, raise a ParseIncomplete exception with the necessary characters to finish the parse.

    Otherwise, return True
    '''

    stack = []

    for c in line:
        matched = False

        # Start a new matching pair
        for left, right in pairs:
            if c == left:
                stack.append(right)
                matched = True
        if matched:
            continue

        # Otherwise, we have a closing character, check the stack
        if c == (top := stack.pop()):
            continue

        # Otherwise, we have a failed match
        raise ParseMismatchException(expected=top, actual=c)

    # If we still have something left to parse, notify
    if stack:
        raise ParseIncompleteException(remaining=''.join(reversed(stack)))

    # Otherwise, yay!
    return True
```

And then we can turn that into a solution!

```python
def part2(file: typer.FileText):

    scores = {')': 1, ']': 2, '}': 3, '>': 4}
    line_scores = []

    for line in file:
        line = line.strip()

        try:
            parse(line)

        except ParseMismatchException:
            pass

        except ParseIncompleteException as ex:
            line_score = 0
            for c in ex.remaining:
                line_score = line_score * 5 + scores[c]

            line_scores.append(line_score)

    print(sorted(line_scores)[len(line_scores) // 2])
```

It would be fun to do a direct base conversion, but this works well enough. 

```bash
$ python3 chunkinator.py part2 input.txt
2776842859
```

And it is of course super fast:

```bash
--- Day 10: Syntax Scoring ---

$ python3 chunkinator.py part1 input.txt
167379
# time 34774792ns / 0.03s

$ python3 chunkinator.py part2 input.txt
2776842859
# time 33728917ns / 0.03s
```

